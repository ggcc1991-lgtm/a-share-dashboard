#!/usr/bin/env python3
"""Merge ForexFactory this-week calendar (USD/CNY/EUR/JPY, High/Medium) into earnings/data/calendar.json.
Only upcoming items are upserted (id prefix ff-); FF has no 'actual' -> fill actual/verdict manually after release.
Usage: python3 earnings/scripts/refresh_macro.py"""
import json,urllib.request,datetime as dt,pathlib
P=pathlib.Path(__file__).resolve().parents[1]/'data'/'calendar.json'
BJ=dt.timezone(dt.timedelta(hours=8))
req=urllib.request.Request('https://nfs.faireconomy.media/ff_calendar_thisweek.json',headers={'User-Agent':'Mozilla/5.0'})
ev=json.load(urllib.request.urlopen(req,timeout=30))
d=json.load(open(P)); macro=[m for m in d['macro'] if not m['id'].startswith('ff-')]
keep={'USD','CNY'}
for e in ev:
    if e['country'] not in keep or e['impact'] not in ('High','Medium'): continue
    t=dt.datetime.fromisoformat(e['date']).astimezone(BJ)
    macro.append({'id':'ff-%s-%s'%(e['country'],t.strftime('%Y%m%d%H%M'))+'-'+''.join(c for c in e['title'] if c.isalnum())[:20],
      'region':'US' if e['country']=='USD' else 'CN','name':e['title'],'releaseAt':t.isoformat(),
      'status':'upcoming' if t>dt.datetime.now(BJ) else 'pending','actual':None,
      'forecast':e.get('forecast') or '暂无','previous':e.get('previous') or '暂无','verdict':None,'diff':None,'impact':e['impact'],
      'source':{'name':'ForexFactory 周历','url':'https://www.forexfactory.com/calendar'}})
d['macro']=macro; d['updated']=dt.datetime.now(BJ).isoformat(timespec='seconds')
json.dump(d,open(P,'w'),ensure_ascii=False,indent=1); print('macro items',len(macro))
