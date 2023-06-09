import time
import requests
from splinter import Browser
from bs4 import BeautifulSoup
from enum import Enum
from datetime import date
from dateutil import relativedelta


class Player_Url(Enum):
    OVERVIEW = "overview"
    BIO = "bio"
    ACTIVITY = "player-activity"
    WIN_LOSS = "fedex-atp-win-loss"
    TITLES_FINALS = "titles-and-finals"
    RANKINGS_HISTORY = "rankings-history"
    RANKINGS_BREAKDOWN = "rankings_breakdown"



class Player:

    #TODO: set config to headless for release
    @staticmethod
    def query_player(name: str):
        base = "https://www.atptour.com/en/players"
        with Browser('chrome', headless=True) as browser:
            browser.visit(base)
            pSearch = browser.find_by_id("playerInput")
            pSearch.fill(name)
            pSearch.click()
            time.sleep(1.0)
            pDropdown = browser.find_by_id("playerDropdown")
            for link in browser.find_by_tag('a'):
                if link.value == name:
                    link.click()
                    return browser.url, BeautifulSoup(browser.html,features='html.parser')

    def swap_link(self,variant:Player_Url):
        return self.base_url + "/" + variant.value

    def __init__(self, name: str) -> object:

        self.country = None
        self.hand = None
        self.backhand = None
        self.titles = []
        self.slams = 0
        self.masters = 0
        self.career_high = 0
        self.web_name = None
        self.active: bool = True
        self.elo: float = 0
        found = False
        while not found:
            self.name = name
            self.web_name = self.name.strip().lower().replace(" ", "-")
            try:
                self.base_url, html = Player.query_player(name)
            except TypeError:
                name = input(name + " not found. Please check the name and enter it again: ")
            else:
                found = True
        hero_table = html.find("div",class_="player-profile-hero-table")
        wraps = [x for x in hero_table.descendants if hasattr(x,"attrs") and "class" in x.attrs and ("wrap" in x["class"])]
        for wrap in wraps:
            edit_var = None
            for div in [ x for x in wrap.contents if x != '\n']:
                match div["class"]:
                    case ["table-big-value"]:
                        if div.span != None:
                            data = div.span.text.strip()
                            match data[-1]:
                                case '\"': self.height = data;
                                case ')': birthdate = data[1:-1].split("."); self.age = relativedelta.relativedelta(date.today(),date(int(birthdate[0]),int(birthdate[1]),int(birthdate[2]))).years;
                                case 's': self.weight = int(data[:-3]);
                    case ["table-value"]:
                        match edit_var:
                            case self.country:
                                try:
                                    self.country = div.contents[0].split(", ")[-1]
                                except IndexError:
                                    self.country = None
                            case self.hand:
                                self.hand = div.contents[0].strip().split("-")[0]
                                self.backhand = div.contents[0].strip().split(" ")[1].strip()

                    case ["table-label"]:
                        match div.contents[0].strip():
                            case "Birthplace": edit_var = self.country
                            case "Plays": edit_var = self.hand

        self.career_high = int(html.find_all(lambda tag: tag.name =="div" and "Career High" in tag.text)[-1].parent.div.contents[0].strip())

        rank_elem = html.find(class_="data-number").contents[0].strip()
        if rank_elem == '':
            self.active = False
            self.rank = self.career_high
        else:
            self.rank = int(rank_elem)
        #TODO: get recent win-loss information
        self.base_url = self.base_url[:-9]
        self.uuid = self.base_url[-4:]
        html = BeautifulSoup(requests.get(self.swap_link(Player_Url.TITLES_FINALS)).text,features='html.parser')
        for link in [x for x in html.find(id="singlesTitles").descendants if x.name=="a"]:
            self.titles.append(link.contents[0].strip())
        for title in self.titles:
            match title:
                case "US Open": self.slams += 1
                case "Roland Garros": self.slams += 1
                case "Wimbledon": self.slams += 1
                case "Australian Open": self.slams += 1
            if "ATP Masters 1000" in title: self.masters += 1
        if self.active:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            elo_html = BeautifulSoup(
                requests.get("https://tennisabstract.com/reports/atp_elo_ratings.html", headers=headers).text,
                features='html.parser')
            for child in elo_html.body.find_all('table')[3].table.contents[1:]:
                td_elements = child.find_all('td')
                test_name = str(td_elements[1].a.text).strip().title().replace(u'\xa0', u' ')
                if str(test_name.strip()) == self.name.strip():
                    self.elo = float(td_elements[3].contents[0])
                    break


    def __str__(self):
        return self.name + " is " + str(self.age) + " and has " + str(self.slams + self.masters) + " major titles and an ELO of " + str(self.elo);