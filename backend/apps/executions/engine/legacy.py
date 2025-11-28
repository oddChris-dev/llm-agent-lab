"""
Legacy Game Engine.

Provides compatibility with the original Flask-based game/session system.
"""

import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import (
    WorkflowEngine,
    ExecutionContext,
    NodeResult,
    NodeStatus,
    ExecutionStatus,
)


class LegacyGameEngine:
    """
    Legacy game engine for turn-based agent workflows.

    Maintains compatibility with the original GameMoves system while
    using the new provider architecture.
    """

    # Command patterns recognized in agent responses
    COMMAND_PATTERN = (
        r'(?P<command>set|search|get|open)\s*'
        r'(?:\(\s*"(?P<payload>[^"]+)"(?:\s*,\s*"(?P<value>[^"]+)")?\s*\)|'
        r':\s*"(?P<colon_payload>[^"]+)"|'
        r'\s+"(?P<no_paren_payload>[^"]+)")'
    )

    # Strings to remove from agent output (UI commands)
    COMMAND_STRINGS = [
        r'^\s*assistant\s*$',
        r'the browser is at this page',
        r'The browser is currently at this page',
        r'the search is complete',
        r'the browser is open to this page',
        r'i have finished speaking',
        r'you have finished speaking'
    ]

    # URL pattern for extracting URLs from text
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'

    def __init__(self, context: ExecutionContext):
        self.context = context
        self.current_player_index = 0

        # Limits for context windows
        self.max_page_body = 8096
        self.max_agent_history = 7
        self.max_link_history = 20
        self.max_page_history = 5
        self.max_search_history = 15
        self.max_user_history = 5
        self.max_settings = 25

    def add_to_history(self, role: str, content: Any):
        """Add entry to conversation history."""
        if content:
            content_str = content if isinstance(content, str) else json.dumps(content)
            history = self.context.get_variable('history', [])
            history.append({
                'role': role,
                'content': content_str,
                'timestamp': datetime.utcnow().isoformat()
            })
            self.context.set_variable('history', history)

    def set_variable(self, name: str, value: Any):
        """Set a session variable."""
        settings = self.context.get_variable('settings', {})
        settings[name] = value
        self.context.set_variable('settings', settings)

    async def do_search(self, search_string: str):
        """Perform a web search."""
        browser = self.context.get_provider('browser')
        if browser:
            try:
                results = await browser.search_async(
                    query=search_string,
                    max_results=10
                )
                # Store search results
                searches = self.context.get_variable('search_results', [])
                searches.extend([r.to_dict() for r in results])
                self.context.set_variable('search_results', searches)
            except Exception as e:
                print(f"do_search exception: {e}")

    async def do_open(self, url: str):
        """Open and fetch a web page."""
        browser = self.context.get_provider('browser')
        if browser:
            try:
                page = await browser.fetch_async(url)

                # Summarize if needed
                if page.body and not self.context.get_variable(f'summary_{url}'):
                    summary = await self.summarize_page(page)
                    self.context.set_variable(f'summary_{url}', summary)

                # Store page
                pages = self.context.get_variable('pages', {})
                pages[url] = page.to_dict()
                self.context.set_variable('pages', pages)

            except Exception as e:
                print(f"do_open exception: {e}")

    async def summarize_page(self, page) -> str:
        """Summarize a web page using LLM."""
        llm = self.context.get_provider('llm')
        if not llm:
            return ''

        from apps.providers.llm.base import LLMMessage

        summary_prompt = self.context.get_variable(
            'summary_prompt',
            "Summarize the following web page content concisely."
        )

        messages = [
            LLMMessage(role='system', content=summary_prompt),
            LLMMessage(role='user', content=json.dumps({
                'url': page.url,
                'title': page.title,
                'body': page.body[:self.max_page_body]
            }))
        ]

        try:
            response = await llm.generate_async(
                messages=messages,
                model=self.context.config.get('model', 'llama3.1:8b'),
                max_tokens=512
            )
            return response.content
        except Exception as e:
            print(f"summarize_page exception: {e}")
            return ''

    def on_page_load(self, url: str, page: Dict[str, Any]):
        """Handle user browser page load event."""
        summary = self.context.get_variable(f'summary_{url}', '')
        if summary:
            self.add_to_history(
                'user',
                f"user is looking at {url}\n\n{summary}"
            )

    def on_user_input(self, user_input: str):
        """Handle user voice/text input."""
        self.add_to_history('user', user_input)

    async def get_response(
        self,
        agent_config: Dict[str, Any],
        input_text: str
    ) -> str:
        """Generate agent response using LLM."""
        llm = self.context.get_provider('llm')
        if not llm:
            return ''

        from apps.providers.llm.base import LLMMessage

        # Get game rules and agent prompt
        game_rules = self.context.get_variable('game_rules', '')
        agent_prompt = self.prepare_prompt(agent_config.get('prompt', ''))

        full_prompt = f"{game_rules}\n\n{agent_prompt}" if game_rules else agent_prompt

        # Build messages with history
        messages = [LLMMessage(role='system', content=full_prompt)]

        # Add conversation history
        history = self.context.get_variable('history', [])
        for entry in history[-self.max_user_history:]:
            if entry['role'] == 'user':
                messages.append(LLMMessage(role='user', content=entry['content']))
            else:
                messages.append(LLMMessage(role='assistant', content=entry['content']))

        messages.append(LLMMessage(role='user', content=input_text))

        try:
            response = await llm.generate_async(
                messages=messages,
                model=agent_config.get('model', 'llama3.1:8b'),
                temperature=agent_config.get('temperature', 0.7),
                max_tokens=agent_config.get('max_tokens', 512)
            )
            return response.content
        except Exception as e:
            print(f"get_response exception: {e}")
            return ''

    def prepare_prompt(self, prompt: str) -> str:
        """
        Prepare agent prompt with variable substitution.

        Supports placeholders like %PAGES%, %SEARCHES%, etc.
        """
        # Pages visited
        if '%PAGES%' in prompt:
            pages = self.context.get_variable('pages', {})
            page_list = list(pages.values())[-self.max_page_history:]
            prompt = prompt.replace('%PAGES%', json.dumps([
                {'title': p.get('title'), 'url': p.get('url'), 'summary': p.get('summary', '')}
                for p in page_list
            ], indent=2))

        # Current page
        if '%CURRENT_PAGE%' in prompt:
            pages = self.context.get_variable('pages', {})
            page_list = list(pages.values())[-1:] if pages else []
            prompt = prompt.replace('%CURRENT_PAGE%', json.dumps([
                {'title': p.get('title'), 'url': p.get('url'), 'summary': p.get('summary', '')}
                for p in page_list
            ], indent=2))

        # Search results
        if '%SEARCHES%' in prompt:
            searches = self.context.get_variable('search_results', [])
            prompt = prompt.replace('%SEARCHES%', json.dumps(
                searches[-self.max_search_history:],
                indent=2
            ))

        # Session settings
        if '%SETTINGS%' in prompt:
            settings = self.context.get_variable('settings', {})
            limited = dict(list(settings.items())[:self.max_settings])
            prompt = prompt.replace('%SETTINGS%', json.dumps(limited, indent=2))

        # Links (unvisited pages)
        if '%LINKS%' in prompt:
            pages = self.context.get_variable('pages', {})
            links = self.context.get_variable('discovered_links', [])
            unvisited = [l for l in links if l.get('url') not in pages]
            prompt = prompt.replace('%LINKS%', json.dumps(
                unvisited[-self.max_link_history:],
                indent=2
            ))

        # Agent history
        if '%AGENTS%' in prompt:
            history = self.context.get_variable('history', [])
            agent_entries = [
                h for h in history
                if h['role'].startswith('agent-')
            ][-self.max_agent_history:]
            prompt = prompt.replace('%AGENTS%', json.dumps(agent_entries, indent=2))

        return prompt

    async def process_turn(self, response: str) -> str:
        """
        Process agent response and execute any commands.

        Extracts and executes commands like search(), open(), set()
        from the agent's response.
        """
        # Process commands
        for match in re.finditer(self.COMMAND_PATTERN, response, re.IGNORECASE):
            command = match.group('command').lower()
            payload = (
                match.group('payload') or
                match.group('colon_payload') or
                match.group('no_paren_payload') or ''
            ).strip()
            payload = re.sub(r'[\"*\']', '', payload)

            value = match.group('value')
            if value:
                value = value.strip()

            try:
                if command == 'set' and value:
                    self.set_variable(payload, value)
                elif command == 'search':
                    await self.do_search(payload)
                elif command in ('get', 'open'):
                    await self.do_open(payload)
            except Exception as e:
                print(f"process_turn {command} exception: {e}")

        # Clean response
        cleaned = re.sub(self.COMMAND_PATTERN, '', response).strip()

        # Remove chat actions (*action*)
        cleaned = re.sub(r'\*\s*[^*]+\s*\*', '', cleaned)

        # Remove command strings
        for cmd_pattern in self.COMMAND_STRINGS:
            cleaned = re.sub(cmd_pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Open any URLs mentioned
        for match in re.finditer(self.URL_PATTERN, cleaned, re.IGNORECASE):
            url = match.group(0)
            await self.do_open(url)

        # Remove URLs from spoken response
        cleaned = re.sub(self.URL_PATTERN, '', cleaned, re.IGNORECASE).strip()

        return cleaned

    async def next_turn(self, previous_response: str = '') -> Optional[str]:
        """
        Execute the next turn in the game.

        Cycles through players and generates their responses.
        """
        players = self.context.get_variable('players', [])
        if not players:
            return None

        # Rotate to next player
        self.current_player_index = (self.current_player_index + 1) % len(players)
        current_player = players[self.current_player_index]

        # Get agent config
        agent_config = self.context.get_variable(
            f'agent_{current_player.get("agent_id")}',
            {}
        )

        # Generate response
        response = await self.get_response(agent_config, previous_response)

        # Add to history
        role = agent_config.get('role', 'assistant')
        self.add_to_history(f'agent-{role}', response)

        # Process commands and clean response
        cleaned_response = await self.process_turn(response)

        # Handle voice output if player has voice
        if current_player.get('voice') and cleaned_response:
            tts = self.context.get_provider('tts')
            if tts:
                from apps.providers.tts.base import TTSRequest
                try:
                    request = TTSRequest(
                        text=cleaned_response,
                        voice_id=current_player.get('voice'),
                        language='en'
                    )
                    await tts.synthesize_async(request)
                except Exception as e:
                    print(f"TTS exception: {e}")

        return response

    async def run_game(self, max_turns: int = 100):
        """
        Run the game loop.

        Continues until max_turns or a stop condition is met.
        """
        response = ''

        for turn in range(max_turns):
            # Check for stop condition
            if self.context.get_variable('stop_game', False):
                break

            try:
                response = await self.next_turn(response) or ''

                # Small delay between turns
                import asyncio
                await asyncio.sleep(1)

            except Exception as e:
                print(f"run_game turn {turn} exception: {e}")
                break
