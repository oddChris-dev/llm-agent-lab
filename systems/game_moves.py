import json
import re

from systems.system_base import SystemBase
from utils.html_tools import HtmlTools
from utils.text_tools import TextTools


class GameMoves(SystemBase):
    def __init__(self, app, session):
        super().__init__(app)

        self.session = session

        self.max_page_body = 8096
        self.max_agent_history = 7
        self.max_link_history = 20
        self.max_page_history = 5
        self.max_search_history = 15
        self.max_user_history = 5
        self.max_settings = 25

        self.current_player_index = 0

        self.command_strings = [
            r'^\s*assistant\s*$',
            r'the browser is at this page',
            r'The browser is currently at this page',
            r'the search is complete',
            r'the browser is open to this page',
            r'i have finished speaking',
            r'you have finished speaking'
        ]

    def add_to_history(self, role, content):
        if content:
            try:
                if isinstance(content, str):
                    content_str = content
                else:
                    content_str = json.dumps(content)

                self.add_session_history(self.session.id, role, content_str)

            except Exception as ex:
                print(f"add_to_history exception {ex}")

    def set_variable(self, name, value):
        setting = self.get_session_setting(self.session.id, name)
        setting.value = value
        setting.save()

    def do_search(self, search_string):
        try:
            print(f"do_search {search_string}")
            self.app.browser().search(self.session.id, search_string)

        except Exception as ex:
            print(f"do_search exception {ex}")

    def do_open(self, url):
        try:
            print(f"do_open {url}")
            page = self.app.browser().fetch(self.session.id, url)
            if page.body and not page.summary:
                self.summarize_page(page)
        except Exception as ex:
            print(f"do_open exception {ex}")

    def summarize_page(self, page):
        try:
            if not page.summary:

                summary_agent = self.get_agent(self.session.summary)

                print(f"summarizing {page.url}")
                page.summary = self.app.text_generator().generate_response(
                    prompt=summary_agent.prompt,
                    input=json.dumps({
                        "url": page.url,
                        "title": page.title,
                        "body": page.body[:self.max_page_body]
                    })
                )

                if page.summary:
                    page.save()

        except Exception as ex:
            print(f"handle_page exception {ex}")

    def on_page_load(self, page):
        print(f"on_page_load {page.url}")
        if not page.summary:
            self.summarize_page(page)
            if page.summary:
                self.add_to_history("user", f"user is looking at {page.url}\n\n{page.summary}")

    def on_user_input(self, user_input):
        self.add_to_history("user", user_input)

    def get_response(self, player, text):
        print(f"generating response for {player.name}")
        response = self.app.text_generator().generate_response(
            prompt=self.get_game(self.session.game).rules + "\n\n" + self.prepare_prompt(player.prompt),
            input=text,
            history=self.get_user_from_history(self.session.id, self.max_user_history))
        return response

    def judge_decision(self, content):
        url = ""

        if content:
            if TextTools.detect_repetition(content):
                entropy = TextTools.calculate_entropy(content)
                print(f"rejected content due to low entropy {entropy}\n {content}")
                return url

            judge = self.get_agent(self.session.judge)
            judge_response = self.get_response(judge, content)

            print(f"the judge says {judge_response}")
            for match in re.finditer(HtmlTools.url_pattern, judge_response, flags=re.IGNORECASE):
                url = match.group(0)  # Get the first matched URL

            if not url:
                print(f"rejected content: {content}")
                self.add_to_history(f"agent-{judge.role}", f"feedback was {judge_response}")

        return url

    def do_turn(self, turn: str = ""):
        #        print(f"processing {tool.name} commands for {response}")

        # Updated regex pattern to capture commands with either one or two values
        pattern = r'(?P<command>set|search|get|open)\s*(?:\(\s*"(?P<payload>[^"]+)"(?:\s*,\s*"(?P<value>[^"]+)")?\s*\)|:\s*"(?P<colon_payload>[^"]+)"|\s+"(?P<no_paren_payload>[^"]+)")'

        for match in re.finditer(pattern, turn, flags=re.IGNORECASE):
            command = match.group('command')
            if command.lower() == 'set':
                variable = (match.group('payload') or
                            match.group('colon_payload') or
                            match.group('no_paren_payload')).strip()
                value = match.group('value').strip() if match.group('value') else None
                payload = {variable: value}
            else:
                payload = (match.group('payload') or
                           match.group('colon_payload') or
                           match.group('no_paren_payload')).strip()

                payload = re.sub(r'[\"*\']', '', payload)

            print(f'Command: {command}')
            print(f'Payload: {payload}')

            try:
                match command.lower():
                    case "set":
                        # Update settings with the variable and value
                        if isinstance(payload, dict):
                            for key, value in payload.items():
                                self.set_variable(key, value)
                        else:
                            print(f'invalid set command: {payload}')
                    case "search":
                        self.do_search(payload)
                    case "get" | "open":
                        self.do_open(payload)
            except Exception as ex:
                print(f"process_commands {command} {payload} exception {ex}")

        # Clean up the response after processing commands
        response = re.sub(pattern, '', turn).strip()
        # remove chat actions
        response = re.sub(r'\*\s*[^*]+\s*\*', '', response)

        # remove command strings
        for command in self.command_strings:
            response = re.sub(command, '', response, flags=re.MULTILINE | re.IGNORECASE)

        # open any urls instead of speaking them
        for match in re.finditer(HtmlTools.url_pattern, response, flags=re.IGNORECASE):
            url = match.group(0)  # Get the matched URL
            self.do_open(url)

        response = re.sub(HtmlTools.url_pattern, '', response, flags=re.IGNORECASE).strip()

        return response

    def prepare_prompt(self, prompt):

        if "%PAGES%" in prompt:
            pages = self.get_pages(self.session.id, self.max_page_history)
            prompt = prompt.replace(
                "%PAGES%",
                json.dumps(
                    [{"title": page.title, "url": page.url, "summary": page.summary} for page in pages],
                    indent=2)
            )
        if "%CURRENT_PAGE%" in prompt:
            pages = self.get_discovered_pages(self.session.id, 1)
            prompt = prompt.replace(
                "%CURRENT_PAGE%",
                json.dumps(
                    [{"title": page.title, "url": page.url, "summary": page.summary} for page in pages],
                    indent=2)
            )
        if "%CURRENT_USER_PAGE%" in prompt:
            pages = self.get_user_pages(self.session.id, 1)
            prompt = prompt.replace(
                "%CURRENT_USER_PAGE%",
                json.dumps(
                    [{"title": page.title, "url": page.url, "summary": page.summary} for page in pages],
                    indent=2)
            )

        if "%SEARCHES%" in prompt:
            results = self.get_search_pages(self.session.id, self.max_search_history)
            prompt = prompt.replace(
                "%SEARCHES%",
                json.dumps(
                    [
                        {"search": page.search_term, "rank": page.search_rank, "title": page.title, "url": page.url}
                        for page in results
                    ],
                    indent=2)
            )
        if "%SETTINGS%" in prompt:
            prompt = prompt.replace(
                "%SETTINGS%",
                json.dumps(
                    self.get_session_settings_limited(self.session.id, self.max_settings),
                    indent=2)
            )
        if "%LINKS%" in prompt:
            pages = self.get_unloaded_pages(self.session.id, self.max_link_history)
            prompt = prompt.replace(
                "%LINKS%",
                json.dumps(
                    [{"title": page.title, "url": page.url} for page in pages],
                    indent=2)
            )
        if "%AGENTS%" in prompt:
            prompt = prompt.replace(
                "%AGENTS%",
                json.dumps(
                    self.get_agents_from_history(self.session.id, self.max_agent_history),
                    indent=2)
            )

        return prompt

    def next_turn(self, previous_response):
        self.session = self.get_session(self.session.id)

        players = self.get_session_players(self.session.id)

        if players:
            # Get current player and rotate to the next player for the next turn
            if not hasattr(self, 'current_player_index'):
                self.current_player_index = 0
            else:
                self.current_player_index = (self.current_player_index + 1) % len(players)

            current_player = players[self.current_player_index]
            current_agent = self.get_agent(current_player.player)

            response = self.get_response(current_agent, previous_response)

            self.add_to_history(f"agent-{current_agent.role}", response)

            turn_response = self.do_turn(response)

            if current_player.voice and turn_response:
                url = self.judge_decision(response)
                if url:
                    # make sure the judge didn't make up a url that doesn't exist
                    page = self.get_session_page(self.session.id, url)
                    if page.title:
                        self.add_session_transcript(self.session.id, url, current_agent.name, response)
                    else:
                        print(f"Judge provided an unknown url {url}")
                else:
                    print("Judge denied the turn")

            return response
