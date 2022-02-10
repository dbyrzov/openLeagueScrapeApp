from django.views.generic import TemplateView
import requests
import json
from datetime import datetime

l_data = ['matchID', 'matchDateTime', 'leagueSeason', 'team1', 'team2', 'matchIsFinished']


class BaseRequest(TemplateView):
    def get_context_data(self, req_url='https://api.openligadb.de/getmatchdata/bl1/2021', **kwargs):
        rec = requests.get(req_url)
        context = super(BaseRequest, self).get_context_data(**kwargs)
        context['j_rec'] = json.loads(rec.text)
        return context

    def winloss(self, teams, single=False):
        rec = requests.get("https://api.openligadb.de/getmatchdata/bl1/2021/")
        matches = json.loads(rec.text)

        for match in matches:
            if match.get('matchIsFinished'):
                t1_goals = match.get('matchResults')[0].get('pointsTeam1')
                t2_goals = match.get('matchResults')[0].get('pointsTeam2')
                t = None
                which_team = None

                if single:
                    if teams.get(match.get('team1').get('teamId')) is not None:
                        t = teams.get(match.get('team1').get('teamId'))
                        which_team = 1
                    elif teams.get(match.get('team2').get('teamId')) is not None:
                        t = teams.get(match.get('team2').get('teamId'))
                        which_team = 2
                    else:
                        continue
                else:
                    t1 = teams.get(match.get('team1').get('teamId'))
                    t2 = teams.get(match.get('team2').get('teamId'))

                if t1_goals > t2_goals:
                    if single:
                        if which_team == 1:
                            t['win'] += 1
                        elif which_team == 2:
                            t['loss'] += 1
                    else:
                        t1['win'] += 1
                        t2['loss'] += 1
                elif t1_goals < t2_goals:
                    if single:
                        if which_team == 1:
                            t['loss'] += 1
                        elif which_team == 2:
                            t['win'] += 1
                    else:
                        t1['loss'] += 1
                        t2['win'] += 1

        return teams

    def next_matches(self, matches):
        curr_date = datetime.now()
        next_dates = [m['matchDateTime'] for m in matches if datetime.strptime(m['matchDateTime'],
                                                                             '%Y-%m-%dT%H:%M:%S') > curr_date]
        next_dates_unique = list(dict.fromkeys(next_dates))
        final_list = [m for m in matches if m['matchDateTime'] == next_dates_unique[0]]

        return final_list


class Index(TemplateView):
    template_name = "index.html"


class Next(BaseRequest):
    template_name = "next_matches.html"

    def get_context_data(self, **kwargs):
        context = super(Next, self).get_context_data(**kwargs)
        j_rec = context.get('j_rec')

        context['matches'] = self.next_matches(j_rec)
        return context


class All(BaseRequest):
    template_name = "all_matches.html"

    def get_context_data(self, **kwargs):
        context = super(All, self).get_context_data(**kwargs)
        j_rec = context.get('j_rec')
        all_dates = \
            [datetime.strptime(m['matchDateTime'], '%Y-%m-%dT%H:%M:%S').date().strftime("%Y-%m-%d") for m in j_rec]
        all_dates_unique = list(dict.fromkeys(all_dates))
        all_dates_unique.sort()
        grouped_matches = []
        for d in all_dates_unique:
            tmp_arr = []
            for m in j_rec:
                if m['matchDateTime'].startswith(d):
                    tmp_arr.append(m)
            grouped_matches.append(tmp_arr)

        context['matches'] = grouped_matches
        return context


class WinLoss(BaseRequest):
    template_name = "winLoss.html"

    def get_context_data(self, **kwargs):
        context = super(WinLoss, self).get_context_data(
            'https://www.openligadb.de/api/getavailableteams/bl1/2021', **kwargs)
        j_rec = context.get('j_rec')
        teams = {team.get('TeamId'): {'win': 0, 'loss': 0, 'name': team.get('TeamName')} for team in j_rec}

        context['teams'] = self.winloss(teams).values()
        return context


class Search(BaseRequest):
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super(Search, self).get_context_data(
            'https://www.openligadb.de/api/getavailableteams/bl1/2021', **kwargs)
        search_word = self.request.GET.get('search', '').lower()
        if search_word == '':
            return context

        teams = context.get('j_rec')
        f_team = {team.get("TeamId"): team.get('TeamName').lower() for team in teams}

        for k, v in f_team.items():
            if v.startswith(search_word):
                the_team = {k: {'win': 0, 'loss': 0, 'name': v}}
                winloss = self.winloss(the_team, True)
                context['teams'] = winloss.values()
                rec = requests.get("https://api.openligadb.de/getmatchdata/bl1/2021/")
                j_rec = json.loads(rec.text)
                matches = []
                for match in j_rec:
                    if match.get('team1').get('teamId') == k:
                        matches.append(match)
                    elif match.get('team2').get('teamId') == k:
                        matches.append(match)

                context['all_matches'] = matches
                next_matches = self.next_matches(matches)
                context['next_matches'] = next_matches
                break

        return context




