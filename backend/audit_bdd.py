import unicodedata
import time
from app.core.database import SessionLocal
from app.models.match import Match
from app.models.team import Team
from app.services.api_football_client import api_football_client
from sqlalchemy import select, update

def normalize(name):
    if not name: return ''
    nfkd = unicodedata.normalize('NFKD', name)
    return nfkd.encode('ascii', 'ignore').decode('ascii').lower().strip()

db = SessionLocal()

BAD_PAIRS = {
    177: (626, 179, 'Leverkusen←Bayern'),
    183: (643, 177, 'Werder←Leverkusen'),
    117: (600, 132, 'Osasuna←Celta'),
    1:   (578, 10,  'Toulouse←Rennes'),
    66:  (533, 84,  'Wolves←WestBrom'),
}

# Charger toutes les équipes pour le matching
all_teams = db.execute(select(Team)).scalars().all()
team_by_name = {normalize(t.name): t for t in all_teams}

total_checked = 0
total_fixed = 0
errors = 0

for wrong_id, (remove_id, correct_id, desc) in BAD_PAIRS.items():
    print(f'\n=== Audit [{wrong_id}] {desc} ===')
    
    matches = db.execute(
        select(Match)
        .where((Match.home_team_id == wrong_id) | (Match.away_team_id == wrong_id))
        .where(Match.api_football_id.isnot(None))
    ).scalars().all()
    
    print(f'{len(matches)} matchs à vérifier')
    
    for m in matches:
        try:
            data = api_football_client._get('/fixtures', params={'id': m.api_football_id})
            total_checked += 1
            fixtures = data.get('response', [])
            
            if not fixtures:
                continue
            
            f = fixtures[0]
            api_home = normalize(f['teams']['home']['name'])
            api_away = normalize(f['teams']['away']['name'])
            
            db_home = db.get(Team, m.home_team_id)
            db_away = db.get(Team, m.away_team_id)
            db_home_name = normalize(db_home.name if db_home else '')
            db_away_name = normalize(db_away.name if db_away else '')
            
            home_match = api_home in db_home_name or db_home_name in api_home
            away_match = api_away in db_away_name or db_away_name in api_away
            
            if not home_match or not away_match:
                # Trouver les bons IDs
                real_home = team_by_name.get(api_home)
                real_away = team_by_name.get(api_away)
                
                if real_home and m.home_team_id != real_home.id:
                    db.execute(update(Match).where(Match.id == m.id).values(home_team_id=real_home.id))
                    total_fixed += 1
                if real_away and m.away_team_id != real_away.id:
                    db.execute(update(Match).where(Match.id == m.id).values(away_team_id=real_away.id))
                    total_fixed += 1
                
                db.commit()
                print(f'  CORRIGÉ match {m.id}: {db_home_name} vs {db_away_name} → {api_home} vs {api_away}')
            
            if total_checked % 50 == 0:
                status = api_football_client.check_status()
                remaining = status.get('requests_remaining', 0)
                print(f'  [quota] {remaining} restantes | {total_checked} vérifiés | {total_fixed} corrigés')
                if remaining < 100:
                    print('Quota critique, arrêt')
                    db.close()
                    exit()
                    
        except Exception as e:
            db.rollback()
            errors += 1
            if errors % 10 == 0:
                print(f'  {errors} erreurs accumulées')

db.close()
print(f'\nDone — {total_checked} vérifiés | {total_fixed} corrigés | {errors} erreurs')
