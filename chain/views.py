"""
Copyright 2019 kivou.2000607@gmail.com

This file is part of yata.

    yata is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    yata is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with yata. If not, see <https://www.gnu.org/licenses/>.
"""

from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseServerError
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string

import traceback
from scipy import stats
import numpy
import json
import random
import os

from player.models import Player

from yata.handy import apiCall
from yata.handy import timestampToDate

from chain.functions import BONUS_HITS
from chain.functions import updateMembers
from chain.functions import factionTree

from chain.models import Faction
from chain.models import Preference
from chain.models import Crontab


# render view
def index(request):
    try:
        if request.session.get('player'):
            print('[view.chain.index] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            key = player.key

            # get user info
            user = apiCall('user', '', 'profile', key)
            if 'apiError' in user:
                context = {'player': player, 'apiError': user["apiError"] + " We can't check your faction so you don't have access to this section."}
                player.chainInfo = "N/A"
                player.factionId = 0
                player.factionNa = "-"
                player.factionAA = False
                # player.lastUpdateTS = int(timezone.now().timestamp())
                player.save()
                return render(request, 'chain.html', context)

            factionId = int(user.get("faction")["faction_id"])
            preferences = Preference.objects.first()
            allowedFactions = json.loads(preferences.allowedFactions) if preferences is not None else []
            print("[view.chain.index] allowedFactions: {}".format(allowedFactions))
            # if str(factionId) in allowedFactions:
            if True:
                player.chainInfo = user.get("faction")["faction_name"]
                player.factionNa = user.get("faction")["faction_name"]
                player.factionId = factionId
                if 'chains' in apiCall('faction', factionId, 'chains', key):
                    player.chainInfo += " [AA]"
                    player.factionAA = True
                else:
                    player.factionAA = False
                # player.lastUpdateTS = int(timezone.now().timestamp())
                player.save()
                print('[view.chain.index] player in faction {}'.format(player.chainInfo))
            else:
                print('[view.chain.index] player in non registered faction {}'.format(user.get("faction")["faction_name"]))
                context = {"player": player, "errorMessage": "Faction not registered. PM Kivou [2000607] for details."}
                return render(request, 'chain.html', context)

            # get /create faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                faction = Faction.objects.create(tId=factionId, name=user.get("faction")["faction_name"])
                print('[view.chain.index] faction {} created'.format(factionId))
                if player.factionAA:
                    minBusy = min([c.nFactions() for c in Crontab.objects.all()])
                    for crontab in Crontab.objects.all():
                        if crontab.nFactions() == minBusy:
                            crontab.faction.add(faction)
                            crontab.save()
                            break
                    print('[view.chain.index] attributed to {} '.format(crontab))
            else:
                faction.name = user.get("faction")["faction_name"]
                faction.save()
                print('[view.chain.index] faction {} found'.format(factionId))

            if player.factionAA:
                print('[view.chain.index] save AA key'.format(factionId))
                faction.addKey(player.tId, player.key)
                faction.save()
            else:
                print('[view.chain.index] remove AA key'.format(factionId))
                faction.delKey(player.tId)
                faction.save()

            chains = faction.chain_set.filter(status=True).order_by('-end')
            context = {'player': player, 'chaincat': True, 'chains': chains, 'view': {'list': True}}
            return render(request, 'chain.html', context)

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


def live(request):
    try:
        if request.session.get('player'):
            print('[view.chain.index] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            factionId = player.factionId
            key = player.key
            page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'

            # get live chain and next bonus
            liveChain = apiCall('faction', factionId, 'chain', key, sub='chain')
            if 'apiError' in liveChain:
                player.chainInfo = "N/A"
                player.factionId = 0
                player.factionAA = False
                # player.lastUpdateTS = int(timezone.now().timestamp())
                player.save()
                selectError = 'apiErrorSub' if request.method == 'POST' else 'apiError'
                context = {'player': player, selectError: liveChain["apiError"] + " We can't check your faction so you don't have access to this section."}
                return render(request, page, context)

            activeChain = bool(int(liveChain['current']) > 9)
            print("[view.chain.index] live chain: {}".format(activeChain))
            liveChain["nextBonus"] = 10
            for i in BONUS_HITS:
                liveChain["nextBonus"] = i
                if i >= int(liveChain["current"]):
                    break

            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Faction not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            if activeChain:
                print('[view.chain.index] chain active')
                chain = faction.chain_set.filter(tId=0).first()
                if chain is None:
                    print('[view.chain.index] live chain 0 created')
                    chain = faction.chain_set.create(tId=0, start=1, status=False)
                else:
                    print('[view.chain.index] live chain 0 found')

                report = chain.report_set.filter(chain=chain).first()
                print('[view.chain.index] live report is {}'.format(report))
                if report is None:
                    chain.graph = ''
                    chain.save()
                    counts = None
                    bonus = None
                    print('[view.chain.index] live counts is {}'.format(counts))
                    print('[view.chain.index] live bonus is {}'.format(bonus))
                else:
                    counts = report.count_set.all()
                    bonus = report.bonus_set.all()
                    print('[view.chain.index] live counts of length {}'.format(len(counts)))
                    print('[view.chain.index] live bonus of length {}'.format(len(bonus)))

                # create graph
                graphSplit = chain.graph.split(',')
                if len(graphSplit) > 1:
                    print('[view.chain.index] data found for graph of length {}'.format(len(graphSplit)))
                    # compute average time for one bar
                    bins = (int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])) / float(60 * (len(graphSplit) - 1))
                    graph = {'data': [], 'info': {'binsTime': bins, 'criticalHits': int(bins) / 5}}
                    cummulativeHits = 0
                    x = numpy.zeros(len(graphSplit))
                    y = numpy.zeros(len(graphSplit))
                    for i, line in enumerate(graphSplit):
                        splt = line.split(':')
                        cummulativeHits += int(splt[1])
                        graph['data'].append([timestampToDate(int(splt[0])), int(splt[1]), cummulativeHits, int(splt[0])])
                        x[i] = int(splt[0])
                        y[i] = cummulativeHits
                    speedRate = cummulativeHits * 300 / float((int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])))  # hits every 5 minutes
                    graph['info']['speedRate'] = speedRate

                    #  y = ax + b (y: hits, x: timestamp)
                    a, b, _, _, _ = stats.linregress(x[-20:], y[-20:])
                    print("[view.chain.index] linreg a={} b={}".format(a, b))
                    a = max(a, 0.00001)
                    ETA = timestampToDate(int((liveChain["nextBonus"] - b) / a))
                    graph['info']['ETALast'] = ETA
                    graph['info']['regLast'] = [a, b]

                    a, b, _, _, _ = stats.linregress(x, y)
                    ETA = timestampToDate(int((liveChain["nextBonus"] - b) / a))
                    graph['info']['ETA'] = ETA
                    graph['info']['reg'] = [a, b]

                else:
                    print('[view.chain.index] no data found for graph')
                    graph = {'data': [], 'info': {'binsTime': 5, 'criticalHits': 1}}

                # context
                context = {'player': player, 'chaincat': True, 'faction': faction, 'chain': chain, 'liveChain': liveChain, 'bonus': bonus, 'counts': counts, 'view': {'report': True, 'liveReport': True}, 'graph': graph}

            # no active chain
            else:
                chain = faction.chain_set.filter(tId=0).first()
                if chain is not None:
                    chain.delete()
                    print('[view.chain.index] chain 0 deleted')
                context = {'player': player, 'chaincat': True, 'faction': faction, 'liveChain': liveChain, 'view': {'liveReport': True}}  # set chain to True to display category links

            return render(request, page, context)

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# render view
def list(request):
    try:
        if request.session.get('player'):
            print('[view.chain.list] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            key = player.key
            factionId = player.factionId
            page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Faction not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            # update chains if AA
            error = False
            if player.factionAA:
                chains = apiCall('faction', faction.tId, 'chains', key, sub='chains')
                if 'apiError' in chains:
                    error = chains

                else:
                    print('[view.chain.list] update chain list')
                    for k, v in chains.items():
                        chain = faction.chain_set.filter(tId=k).first()
                        if v['chain'] >= faction.hitsThreshold:
                            if chain is None:
                                # print('[view.chain.list] chain {} created'.format(k))
                                faction.chain_set.create(tId=k, nHits=v['chain'], respect=v['respect'],
                                                         start=v['start'],
                                                         end=v['end'])
                            else:
                                # print('[view.chain.list] chain {} updated'.format(k))
                                chain.start = v['start']
                                chain.end = v['end']
                                chain.nHits = v['chain']
                                # chain.reportNHits = 0
                                chain.respect = v['respect']
                                chain.save()

                        else:
                            if chain is not None:
                                # print('[view.chain.list] chain {} deleted'.format(k))
                                chain.delete()

            # get chains
            chains = faction.chain_set.filter(status=True).order_by('-end')

            context = {'player': player, 'chaincat': True, 'chains': chains, 'view': {'list': True}}
            if error:
                selectError = 'apiErrorSub' if request.method == 'POST' else 'apiError'
                context.update({selectError: error["apiError"] + " List of chain not updated."})
            return render(request, page, context)

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# render view
def report(request, chainId):
    try:
        if request.session.get('player'):
            print('[view.chain.list] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            factionId = player.factionId
            page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Faction not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            chains = faction.chain_set.filter(status=True).order_by('-end')

            # get chain
            chain = faction.chain_set.filter(tId=chainId).first()
            if chain is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Chain not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            print('[view.chain.report] chain {} found'.format(chainId))

            # get report
            report = chain.report_set.filter(chain=chain).first()
            if report is None:
                print('[view.chain.report] report of {} not found'.format(chain))
                context = dict({"player": player, 'chaincat': True, 'chain': chain, 'chains': chains, 'view': {'report': True, 'list': True}})
                return render(request, page, context)

            print('[view.chain.report] report of {} found'.format(chain))

            # create graph
            graphSplit = chain.graph.split(',')
            if len(graphSplit) > 1:
                print('[view.chain.report] data found for graph of length {}'.format(len(graphSplit)))
                # compute average time for one bar
                bins = (int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])) / float(60 * (len(graphSplit) - 1))
                graph = {'data': [], 'info': {'binsTime': bins, 'criticalHits': int(bins) / 5}}
                cummulativeHits = 0
                for line in graphSplit:
                    splt = line.split(':')
                    cummulativeHits += int(splt[1])
                    graph['data'].append([timestampToDate(int(splt[0])), int(splt[1]), cummulativeHits])
                    speedRate = cummulativeHits * 300 / float((int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])))  # hits every 5 minutes
                    graph['info']['speedRate'] = speedRate
            else:
                print('[view.chain.report] no data found for graph')
                graph = {'data': [], 'info': {'binsTime': 5, 'criticalHits': 1, 'speedRate': 0}}

            # context
            context = dict({"player": player,
                            'chaincat': True,
                            'chain': chain,  # for general info
                            'chains': chains,  # for chain list after report
                            'counts': report.count_set.all(),  # for report
                            'bonus': report.bonus_set.all(),  # for report
                            'graph': graph,  # for report
                            'view': {'list': True, 'report': True}})  # views

            return render(request, page, context)

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# render view
def jointReport(request):
    try:
        if request.session.get('player'):
            print('[view.chain.list] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            key = player.key
            factionId = player.factionId
            page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Faction not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            # get chains
            chains = faction.chain_set.filter(jointReport=True).order_by('start')
            print('[VIEW jointReport] {} chains for the joint report'.format(len(chains)))
            if len(chains) < 1:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {selectError: 'No chains found for the joint report. Add reports throught the chain list.',
                           'chains': faction.chain_set.filter(status=True).order_by('-end'),
                           'player': player, 'chaincat': True, 'view': {'list': True}}
                return render(request, page, context)

            # loop over chains
            counts = dict({})
            bonuses = dict({})
            total = {'nHits': 0, 'respect': 0.0}
            for chain in chains:
                print('[VIEW jointReport] chain {} found'.format(chain.tId))
                total['nHits'] += chain.nHits
                total['respect'] += float(chain.respect)
                # get report
                report = chain.report_set.filter(chain=chain).first()
                if report is None:
                    return render(request, 'yata/error.html', {'errorMessage': 'Report of chain {} not found in the database.'.format(chain.tId)})
                print('[VIEW jointReport] report of {} found'.format(chain))
                # loop over counts
                chainCounts = report.count_set.all()
                chainBonuses = report.bonus_set.all()
                for bonus in chainBonuses:
                    if bonus.tId in bonuses:
                        bonuses[bonus.tId][1].append(bonus.hit)
                        bonuses[bonus.tId][2] += bonus.respect
                    else:
                        bonuses[bonus.tId] = [bonus.name, [bonus.hit], bonus.respect, 0]

                for count in chainCounts:

                    if count.attackerId in counts:
                        counts[count.attackerId]['hits'] += count.hits
                        counts[count.attackerId]['wins'] += count.wins
                        counts[count.attackerId]['respect'] += count.respect
                        counts[count.attackerId]['fairFight'] += count.fairFight
                        counts[count.attackerId]['war'] += count.war
                        counts[count.attackerId]['retaliation'] += count.retaliation
                        counts[count.attackerId]['groupAttack'] += count.groupAttack
                        counts[count.attackerId]['overseas'] += count.overseas
                        counts[count.attackerId]['watcher'] += count.watcher / float(len(chains))
                        counts[count.attackerId]['beenThere'] = count.beenThere or counts[count.attackerId]['beenThere']  # been present to at least one chain
                    else:
                        counts[count.attackerId] = {'name': count.name,
                                                    'hits': count.hits,
                                                    'wins': count.wins,
                                                    'respect': count.respect,
                                                    'fairFight': count.fairFight,
                                                    'war': count.war,
                                                    'retaliation': count.retaliation,
                                                    'groupAttack': count.groupAttack,
                                                    'overseas': count.overseas,
                                                    'watcher': count.watcher / float(len(chains)),
                                                    'daysInFaction': count.daysInFaction,
                                                    'beenThere': count.beenThere,
                                                    'attackerId': count.attackerId}
                print('[VIEW jointReport] {} counts for {}'.format(len(counts), chain))

            # order the Bonuses
            # bonuses ["name", [[bonus1, bonus2, bonus3, ...], respect, nwins]]
            smallHit = 999999999
            for k, v in counts.items():
                if k in bonuses:
                    if v["daysInFaction"] >= 0:
                        bonuses[k][3] = v["wins"]
                        smallHit = min(int(v["wins"]), smallHit)
                    else:
                        del bonuses[k]

            for k, v in counts.items():
                if k not in bonuses and int(v["wins"]) >= smallHit and v["daysInFaction"] >= 0:
                    bonuses[k] = [v["name"], [], 0, v["wins"]]

                # else:
                #     if int(v["wins"]) >= int(smallestNwins):
                #         bonuses.append([[v["name"]], [[], 1, v["wins"]]])

            # aggregate counts
            arrayCounts = [v for k, v in counts.items()]
            arrayBonuses = [[i, name, ", ".join([str(h) for h in sorted(hits)]), respect, wins] for i, (name, hits, respect, wins) in sorted(bonuses.items(), key=lambda x: x[1][1], reverse=True)]

            # add last time connected
            error = False
            update = updateMembers(faction, key=key)
            if 'apiError' in update:
                error = update

            for i, bonus in enumerate(arrayBonuses):
                try:
                    arrayBonuses[i].append(faction.member_set.filter(tId=bonus[0]).first().lastAction)
                except:
                    arrayBonuses[i].append(False)

            # context
            context = dict({'chainsReport': chains,  # chains of joint report
                            'total': total,  # for general info
                            'counts': arrayCounts,  # counts for report
                            'bonuses': arrayBonuses,  # bonuses for report
                            'chains': faction.chain_set.filter(status=True).order_by('-end'),  # for chain list after report
                            'player': player,
                            'chaincat': True,  # to display categories
                            'view': {'jointReport': True}})  # view

            if error:
                selectError = 'apiErrorSub' if request.method == 'POST' else 'apiError'
                context.update({selectError: error["apiError"] + " List of members not updated."})
            return render(request, page, context)

        else:
            message = "You might want to log in." if request.method == "POST" else "You need to post. Don\'t try to be a smart ass."
            raise PermissionDenied(message)

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# render view
def members(request):
    try:
        if request.session.get('player'):
            print('[view.chain.members] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            key = player.key
            factionId = player.factionId
            page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                selectError = 'errorMessageSub' if request.method == 'POST' else 'errorMessage'
                context = {'player': player, selectError: "Faction not found. It might come from a API issue. Click on chain report again please."}
                return render(request, page, context)

            # update chains if AA
            members = updateMembers(faction, key=key)
            error = False
            if 'apiError' in members:
                error = members

            # get members
            members = faction.member_set.all()

            context = {'player': player, 'chaincat': True, 'faction': faction, 'members': members, 'view': {'members': True}}
            if error:
                selectError = 'apiErrorSub' if request.method == 'POST' else 'apiError'
                context.update({selectError: error["apiError"] + " Members not updated."})
            return render(request, page, context)

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# action view
def createReport(request, chainId):
    try:
        if request.session.get('player') and request.method == 'POST':
            print('[view.chain.createReport] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()

            factionId = player.factionId
            context = {"player": player}

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Faction {} not found in the database.'.format(factionId)})

            # get chain
            chain = faction.chain_set.filter(tId=chainId).first()
            if chain is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Chain {} not found in the database.'.format(chainId)})
            print('[view.chain.createReport] chain {} found'.format(chainId))

            print('[view.chain.createReport] number of hits: {}'.format(chain.nHits))
            chain.createReport = True
            chain.save()
            context = {"player": player, "chain": chain}
            return render(request, 'chain/list-buttons.html', context)

        else:
            message = "You might want to log in." if request.method == "POST" else "You need to post. Don\'t try to be a smart ass."
            raise PermissionDenied(message)

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# action view
def renderIndividualReport(request, chainId, memberId):
    try:
        if request.session.get('player') and request.method == 'POST':
            # get session info
            print('[view.chain.renderIndividualReport] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            factionId = player.factionId

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Faction {} not found in the database.'.format(factionId)})
            print('[view.chain.renderIndividualReport] faction {} found'.format(factionId))

            # get chain
            chain = faction.chain_set.filter(tId=chainId).first()
            if chain is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Chain {} not found in the database.'.format(chainId)})
            print('[view.chain.renderIndividualReport] chain {} found'.format(chainId))

            # get report
            report = chain.report_set.filter(chain=chain).first()
            if report is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Report of chain {} not found in the database.'.format(chainId)})
            print('[view.chain.renderIndividualReport] report of {} found'.format(chain))

            # create graph
            count = report.count_set.filter(attackerId=memberId).first()
            graphSplit = count.graph.split(',')
            if len(graphSplit) > 1:
                print('[view.chain.renderIndividualReport] data found for graph of length {}'.format(len(graphSplit)))
                # compute average time for one bar
                bins = (int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])) / float(60 * (len(graphSplit) - 1))
                graph = {'data': [], 'info': {'binsTime': bins, 'criticalHits': int(bins) / 5}}
                cummulativeHits = 0
                for line in graphSplit:
                    splt = line.split(':')
                    cummulativeHits += int(splt[1])
                    graph['data'].append([timestampToDate(int(splt[0])), int(splt[1]), cummulativeHits])
                    speedRate = cummulativeHits * 300 / float((int(graphSplit[-1].split(':')[0]) - int(graphSplit[0].split(':')[0])))  # hits every 5 minutes
                    graph['info']['speedRate'] = speedRate
            else:
                print('[view.chain.report] no data found for graph')
                graph = {'data': [], 'info': {'binsTime': 5, 'criticalHits': 1, 'speedRate': 0}}

            # context
            context = dict({'graph': graph,  # for report
                            'memberId': memberId})  # for selecting to good div

            print('[view.chain.renderIndividualReport] render')
            return render(request, 'chain/ireport.html', context)

        else:
            message = "You might want to log in." if request.method == "POST" else "You need to post. Don\'t try to be a smart ass."
            raise PermissionDenied(message)

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# action view
def deleteReport(request, chainId):
    try:
        if request.session.get('player') and request.method == 'POST':
            print('[view.chain.deleteReport] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            factionId = player.factionId
            context = {"player": player}

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Faction {} not found in the database.'.format(factionId)})

            # get chain
            chain = faction.chain_set.filter(tId=chainId).first()
            if chain is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Chain {} not found in the database.'.format(chainId)})
            print('[view.chain.deleteReport] chain {} found'.format(chainId))

            # delete old report and remove from joint report
            chain.report_set.all().delete()
            chain.jointReport = False
            chain.createReport = False
            chain.hasReport = False
            chain.save()

            context = {"player": player, "chain": chain}
            return render(request, 'chain/list-buttons.html', context)

        else:
            message = "You might want to log in." if request.method == "POST" else "You need to post. Don\'t try to be a smart ass."
            raise PermissionDenied(message)

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


# action view
def toggleReport(request, chainId):
    try:
        if request.session.get('player') and request.method == 'POST':
            print('[view.chain.deleteReport] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            factionId = player.factionId
            context = {"player": player}

            # get faction
            faction = Faction.objects.filter(tId=factionId).first()
            if faction is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Faction {} not found in the database.'.format(factionId)})
            print('[VIEW toggleReport] faction {} found'.format(factionId))

            # get chain
            chain = faction.chain_set.filter(tId=chainId).first()
            if chain is None:
                return render(request, 'yata/error.html', {'errorMessage': 'Chain {} not found in the database.'.format(chainId)})
            print('[VIEW toggleReport] chain {} found'.format(chainId))

            # toggle
            chain.toggle_report()
            chain.save()

            print('[VIEW toggleReport] render')
            context.update({"chain": chain})
            return render(request, 'chain/list-buttons.html', context)

        else:
            message = "You might want to log in." if request.method == "POST" else "You need to post. Don\'t try to be a smart ass."
            raise PermissionDenied(message)

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


def crontab(request):
    try:
        if request.session.get('player'):
            print('[view.chain.crontab] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            if player.factionAA:
                faction = Faction.objects.filter(tId=player.factionId).first()
                print('[view.chain.crontab] player with AA. Faction {}'.format(faction))
                crontabs = dict({})
                for crontab in faction.crontab_set.all():
                    print('[view.chain.crontab]     --> {}'.format(crontab))
                    crontabs[crontab.tabNumber] = {"crontab": crontab, "factions": []}
                    for f in crontab.faction.all():
                        crontabs[crontab.tabNumber]["factions"].append(f)
                context = {'player': player, 'chaincat': True, 'crontabs': crontabs, 'view': {'crontab': True}}
                page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'
                return render(request, page, context)

            else:
                raise PermissionDenied("You need AA rights.")

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))


def tree(request):
    try:
        if request.session.get('player'):
            print('[view.chain.tree] get player id from session')
            tId = request.session["player"].get("tId")
            player = Player.objects.filter(tId=tId).first()
            player.lastActionTS = int(timezone.now().timestamp())
            player.save()

            if player.factionAA:
                faction = Faction.objects.filter(tId=player.factionId).first()
                print('[view.chain.tree] player with AA. Faction {}'.format(faction))

                if request.method == "POST":
                    t = request.POST.get("t", False)
                    p = int(request.POST.get("p", False))
                    v = int(request.POST.get("v", False))
                    if t:
                        print('[view.chain.tree] {}[{}] = {}'.format(t, p, v))
                        posterOpt = json.loads(faction.posterOpt)
                        if posterOpt.get(t, False):
                            posterOpt[t][p] = v
                        else:
                            if t == "fontColor":
                                option = [0, 0, 0, 255]
                                option[p] = v
                            elif t == "fontFamily":
                                option = [0]
                                option[p] = v
                            elif t == "iconType":
                                option = [0]
                                option[p] = v
                            elif t == "background":
                                option = [0, 0, 0, 0]
                                option[p] = v

                            posterOpt[t] = option

                        faction.posterOpt = json.dumps(posterOpt)
                        faction.save()

                factionTree(faction)

                fntId = {i: [f.split("__")[0].replace("-", " "), int(f.split("__")[1].split(".")[0])] for i, f in enumerate(sorted(os.listdir(settings.STATIC_ROOT + '/perso/font/')))}
                posterOpt = json.loads(faction.posterOpt)
                context = {'player': player, 'chaincat': True, 'faction': faction, "posterOpt": posterOpt, 'random': random.randint(0, 65535), 'fonts': fntId, 'view': {'tree': True}}
                page = 'chain/content-reload.html' if request.method == 'POST' else 'chain.html'
                return render(request, page, context)

            else:
                raise PermissionDenied("You need AA rights.")

        else:
            raise PermissionDenied("You might want to log in.")

    except Exception:
        print("[ERROR] {}".format(traceback.format_exc()))
        return HttpResponseServerError(render_to_string('500.html', {'exception': traceback.format_exc().strip()}))
