#!/usr/bin/env python
"""
Legacy Data Migration Script.

Migrates data from the old Flask/MySQL database to the new Django/PostgreSQL database.

Usage:
    python migrate_legacy_data.py --source mysql://user:pass@host/dbname

Requirements:
    - MySQL connector: pip install mysql-connector-python
    - Django settings configured
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for Django settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
import mysql.connector


User = get_user_model()


class LegacyMigrator:
    """Handles migration of legacy Flask data to Django."""

    def __init__(self, mysql_config: Dict[str, str], default_user_id: int = None):
        """
        Initialize migrator.

        Args:
            mysql_config: MySQL connection config dict
            default_user_id: Default user ID to assign migrated data to
        """
        self.mysql_config = mysql_config
        self.default_user_id = default_user_id
        self.connection = None
        self.cursor = None

        # ID mappings from old to new
        self.agent_map: Dict[int, str] = {}
        self.voice_map: Dict[int, str] = {}
        self.game_map: Dict[int, str] = {}
        self.session_map: Dict[int, str] = {}

    def connect(self):
        """Connect to legacy MySQL database."""
        self.connection = mysql.connector.connect(**self.mysql_config)
        self.cursor = self.connection.cursor(dictionary=True)
        print("Connected to legacy MySQL database")

    def disconnect(self):
        """Close MySQL connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Disconnected from legacy database")

    def get_or_create_user(self) -> User:
        """Get or create the default migration user."""
        if self.default_user_id:
            return User.objects.get(id=self.default_user_id)

        user, created = User.objects.get_or_create(
            username='legacy_migration',
            defaults={
                'email': 'migration@localhost',
                'is_active': True,
            }
        )
        if created:
            print(f"Created migration user: {user.username}")
        return user

    def migrate_agents(self, user: User):
        """Migrate agent table to new Agent model."""
        from apps.workflows.models_legacy import Agent

        self.cursor.execute("SELECT * FROM agent")
        agents = self.cursor.fetchall()

        print(f"Migrating {len(agents)} agents...")

        for row in agents:
            agent = Agent.objects.create(
                name=row['name'],
                prompt=row.get('prompt', ''),
                role=row.get('role', ''),
                user=user,
                default_model=row.get('model', 'llama3.1:8b'),
                default_temperature=row.get('temperature', 0.7),
                default_max_tokens=row.get('max_tokens', 512),
            )
            self.agent_map[row['id']] = str(agent.id)
            print(f"  Migrated agent: {agent.name}")

    def migrate_voices(self, user: User):
        """Migrate voice table to Asset model."""
        from apps.assets.models import Asset

        self.cursor.execute("SELECT * FROM voice")
        voices = self.cursor.fetchall()

        print(f"Migrating {len(voices)} voices...")

        for row in voices:
            # Create asset for voice sample
            asset = Asset.objects.create(
                name=row['name'],
                asset_type='voice',
                user=user,
                metadata={
                    'legacy_id': row['id'],
                    'original_name': row['name'],
                }
            )

            # Store binary data if present
            if row.get('data'):
                asset.file.save(
                    f"{row['name']}.wav",
                    ContentFile(row['data']),
                    save=True
                )

            self.voice_map[row['id']] = str(asset.id)
            print(f"  Migrated voice: {asset.name}")

    def migrate_games(self, user: User):
        """Migrate game templates to GameTemplate model."""
        from apps.workflows.models_legacy import GameTemplate

        self.cursor.execute("SELECT * FROM game")
        games = self.cursor.fetchall()

        print(f"Migrating {len(games)} game templates...")

        for row in games:
            template = GameTemplate.objects.create(
                name=row['name'],
                rules=row.get('rules', ''),
                description=row.get('description', ''),
                user=user,
                default_settings=json.loads(row.get('default_settings', '{}')),
            )
            self.game_map[row['id']] = str(template.id)
            print(f"  Migrated game template: {template.name}")

    def migrate_sessions(self, user: User):
        """Migrate sessions to Execution model."""
        from apps.executions.models import Execution
        from apps.workflows.models import Workflow

        self.cursor.execute("SELECT * FROM session")
        sessions = self.cursor.fetchall()

        print(f"Migrating {len(sessions)} sessions...")

        for row in sessions:
            # Create a workflow for legacy session
            workflow = Workflow.objects.create(
                name=f"Legacy Session: {row.get('name', row['id'])}",
                description="Migrated from legacy session",
                user=user,
                is_template=False,
                settings={
                    'legacy_game_id': row.get('game'),
                    'legacy_session_id': row['id'],
                }
            )

            # Create execution record
            execution = Execution.objects.create(
                workflow=workflow,
                status='completed',
                started_at=row.get('created_at', datetime.utcnow()),
                completed_at=row.get('updated_at'),
                context={
                    'legacy_summary_agent': row.get('summary'),
                    'legacy_judge_agent': row.get('judge'),
                },
                user=user,
            )

            self.session_map[row['id']] = str(execution.id)
            print(f"  Migrated session: {row['id']}")

            # Migrate session players
            self.migrate_session_players(row['id'], execution, user)

            # Migrate session history
            self.migrate_session_history(row['id'], execution)

            # Migrate pages
            self.migrate_pages(row['id'], execution)

            # Migrate transcripts
            self.migrate_transcripts(row['id'], execution)

    def migrate_session_players(self, session_id: int, execution, user):
        """Migrate session_player records."""
        from apps.workflows.models_legacy import GamePlayer

        self.cursor.execute(
            "SELECT * FROM session_player WHERE session = %s",
            (session_id,)
        )
        players = self.cursor.fetchall()

        for row in players:
            agent_id = self.agent_map.get(row.get('player'))
            voice_id = self.voice_map.get(row.get('voice'))

            player = GamePlayer.objects.create(
                name=row.get('name', 'Player'),
                execution=execution,
                agent_id=agent_id,
                voice_id=voice_id,
                turn_order=row.get('turn_order', 0),
                is_active=row.get('is_active', True),
                user=user,
            )

    def migrate_session_history(self, session_id: int, execution):
        """Migrate session_history records to execution logs."""
        self.cursor.execute(
            "SELECT * FROM session_history WHERE session = %s ORDER BY id",
            (session_id,)
        )
        history = self.cursor.fetchall()

        logs = []
        for row in history:
            logs.append({
                'role': row.get('role', 'system'),
                'content': row.get('content', ''),
                'timestamp': row.get('created_at', datetime.utcnow()).isoformat()
                    if row.get('created_at') else datetime.utcnow().isoformat(),
            })

        # Store as execution context
        context = execution.context or {}
        context['history'] = logs
        execution.context = context
        execution.save()

    def migrate_pages(self, session_id: int, execution):
        """Migrate page records to WebPage model."""
        from apps.workflows.models_legacy import WebPage
        import hashlib

        self.cursor.execute(
            "SELECT * FROM page WHERE session = %s",
            (session_id,)
        )
        pages = self.cursor.fetchall()

        for row in pages:
            url = row.get('url', '')
            url_hash = hashlib.sha256(url.encode()).hexdigest()[:64]

            WebPage.objects.create(
                execution=execution,
                url=url,
                url_hash=url_hash,
                title=row.get('title', ''),
                body=row.get('body', ''),
                summary=row.get('summary', ''),
                parent_url_hash=row.get('parent_url_hash', ''),
                search_term=row.get('search_term', ''),
                search_rank=row.get('search_rank'),
            )

    def migrate_transcripts(self, session_id: int, execution):
        """Migrate session_transcript records to Transcript model."""
        from apps.workflows.models_legacy import Transcript

        self.cursor.execute(
            "SELECT * FROM session_transcript WHERE session = %s",
            (session_id,)
        )
        transcripts = self.cursor.fetchall()

        for row in transcripts:
            Transcript.objects.create(
                execution=execution,
                url=row.get('url', ''),
                agent_name=row.get('agent', ''),
                content=row.get('content', ''),
                audio_url=row.get('audio_url', ''),
            )

    @transaction.atomic
    def run(self):
        """Run the full migration."""
        print("=" * 60)
        print("Starting Legacy Data Migration")
        print("=" * 60)

        try:
            self.connect()
            user = self.get_or_create_user()

            print("\n--- Phase 1: Core Entities ---")
            self.migrate_agents(user)
            self.migrate_voices(user)
            self.migrate_games(user)

            print("\n--- Phase 2: Sessions and Related Data ---")
            self.migrate_sessions(user)

            print("\n" + "=" * 60)
            print("Migration Complete!")
            print("=" * 60)
            print(f"  Agents migrated: {len(self.agent_map)}")
            print(f"  Voices migrated: {len(self.voice_map)}")
            print(f"  Games migrated: {len(self.game_map)}")
            print(f"  Sessions migrated: {len(self.session_map)}")

        except Exception as e:
            print(f"\nMigration failed: {e}")
            raise

        finally:
            self.disconnect()

    def export_mappings(self, filepath: str):
        """Export ID mappings to JSON file."""
        mappings = {
            'agents': self.agent_map,
            'voices': self.voice_map,
            'games': self.game_map,
            'sessions': self.session_map,
        }
        with open(filepath, 'w') as f:
            json.dump(mappings, f, indent=2)
        print(f"ID mappings exported to {filepath}")


def parse_mysql_url(url: str) -> Dict[str, Any]:
    """Parse MySQL connection URL to config dict."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 3306,
        'user': parsed.username or 'root',
        'password': parsed.password or '',
        'database': parsed.path.lstrip('/'),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Migrate legacy Flask/MySQL data to Django/PostgreSQL'
    )
    parser.add_argument(
        '--source',
        required=True,
        help='MySQL connection URL (mysql://user:pass@host/db)'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='Django user ID to assign migrated data to'
    )
    parser.add_argument(
        '--export-mappings',
        help='Path to export ID mappings JSON'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )

    args = parser.parse_args()

    mysql_config = parse_mysql_url(args.source)
    print(f"Source database: {mysql_config['host']}/{mysql_config['database']}")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")
        # Just connect and show counts
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        tables = ['agent', 'voice', 'game', 'session', 'page', 'session_history']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")

        cursor.close()
        conn.close()
        return

    migrator = LegacyMigrator(mysql_config, args.user_id)
    migrator.run()

    if args.export_mappings:
        migrator.export_mappings(args.export_mappings)


if __name__ == '__main__':
    main()
