import scrapy, logging

class FlamengoSpider(scrapy.Spider):
    name = 'flamengo'
    allowed_domains = ['ogol.com.br']
    start_urls = ['https://www.ogol.com.br/equipe/flamengo']  # Keep the main page for players
    matches_url = 'https://www.ogol.com.br/equipe/flamengo/todos-os-jogos?grp=1' # New URL for matches

    def parse(self, response):
        # with open("flamengo_page.html", "wb") as f:
        #     f.write(response.body)
        # Extract players (this part remains the same)
        players = []
        for player_div in response.css('#team_squad div.staff'):
            name = player_div.css('div.name a::text').get()
            if name:
                name = name.strip()
            players.append(name)
        players = list(filter(None, players))  # Remove empty strings or None values
        yield {'players': players}

        # Request the matches URL and parse it with a different method
        yield scrapy.Request(self.matches_url, callback=self.parse_matches)

    def parse_matches(self, response):
        matches = []
        team_games_div = response.css('#team_games')

        if team_games_div:
            matches_table = team_games_div.css('table.zztable.stats')

            if matches_table:
                for match_row in matches_table.css('tbody tr')[6:]:
                    date = match_row.css('td.double::text').get(default=None)
                    opponent_team = match_row.css('td.text a::text').get(default=None)
                    result = match_row.css('td.result a::text').get(default=None)
                    championship = match_row.css('td.text div.micrologo_and_text a::text').get(default=None)

                    # Clean data
                    if date:
                        date = date.strip()
                    if opponent_team:
                        opponent_team = opponent_team.strip()
                    if result:
                        result = result.strip()

                    matches.append({
                        'date': date,
                        'opponent': opponent_team,
                        'result': result,
                        'championship': championship
                    })
                else:
                    self.log('Error: Matches table with class "zztable stats" not found within #team_games!', level=logging.ERROR)
            else:
                self.log('Error: div#team_games not found!', level=logging.ERROR)

            yield {'matches': matches}