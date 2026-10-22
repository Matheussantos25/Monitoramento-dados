"""Synthetic parity fixtures; never reads user records or secrets."""
import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from solem_training_cycle import START, END, cycle_day, cycle_base_goals
from tests.test_training_cycle import record, completed_week

history=[record(i,START-timedelta(days=i),"Barra Fixa (Pronada)",15,3) for i in (1,2)]
week1=completed_week([],0,0)
week2=completed_week(week1,1,1)
cases=[]
for name,rows,day in [
    ("first_strength",[],START+timedelta(days=1)),
    ("walk",[record(1,START,"Caminhada",km=2),record(2,START,"Corrida",km=3)],START),
    ("rest",[],START+timedelta(days=2)),
    ("pull_fallback",[],START+timedelta(days=6)),
    ("pull_history",history,START+timedelta(days=6)),
    ("week2_held",[],START+timedelta(days=8)),
    ("week2_advanced",week1,START+timedelta(days=8)),
    ("week3_advanced",week2,START+timedelta(days=15)),
    ("deload",[],START+timedelta(days=22)),
    ("end",week2,END+timedelta(days=1)),
]:
    plan=cycle_day(rows,day)
    base=cycle_base_goals(rows,day)
    cases.append(dict(name=name,records=rows,day=str(day),expected=dict(
        active=plan["active"],stage=plan["stage"],week=plan["cycle_week"],held=plan["held"],
        percent=plan["percent"],recovery=plan["recovery"],completed=plan["completed"],
        goals=[dict(exercise=g["exercise"],target=g["target"],sets=g["sets"],value=g["value"],unit=g["unit"]) for g in plan["goals"]],
        base=[dict(exercise=g["exercise"],target=g["target"],value=g["value"]) for g in base])))
target=ROOT/"android-app/app/src/test/resources/training_cycle_parity.json"
target.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(f"Generated {len(cases)} synthetic cycle parity cases")
