import os
import requests
import json
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

class LostArkAPI:
    def __init__(self):
        self.api_key = os.getenv("LOA_API_KEY") 
        self.token = self.api_key 
        self.headers = {
            'accept': 'application/json',
            'authorization': f'bearer {self.api_key}'
        }
        self.base_url = "https://developer-lostark.game.onstove.com"

    def get_character_profile(self, char_name):
        url = f"{self.base_url}/armories/characters/{char_name}/profiles"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def get_characters(self, representative_name):
        representative_name = representative_name.strip()
        
        # 1. 원정대 목록 조회
        siblings_url = f"{self.base_url}/characters/{representative_name}/siblings"
        try:
            resp = requests.get(siblings_url, headers=self.headers)
            if resp.status_code != 200:
                print(f"⚠️ 원정대 조회 실패: {resp.status_code}")
                return []
            siblings = resp.json()
            if not siblings: return []
        except Exception as e:
            print(f"❌ API 요청 에러: {e}")
            return []

        # 2. 상세 정보 병렬 조회
        enriched_data = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_char = {
                executor.submit(self.get_character_profile, char['CharacterName']): char 
                for char in siblings
            }
            
            for future in concurrent.futures.as_completed(future_to_char):
                char_basic = future_to_char[future]
                profile_detail = future.result()
                
                combat_power = 0
                
                if profile_detail:
                    # [수정됨] CombatPower 파싱 로직 강화 (쉼표와 소수점 처리)
                    # "1,743.76" -> 1743
                    if 'CombatPower' in profile_detail:
                        try:
                            raw_val = str(profile_detail['CombatPower']) # 일단 문자열로
                            clean_val = raw_val.replace(',', '')         # 쉼표 제거 "1743.76"
                            combat_power = int(float(clean_val))         # 실수 변환 후 정수화
                        except:
                            combat_power = 0
                    
                    # (만약 CombatPower가 0이면 예비로 공격력 가져오기 - 혹시 모르니 유지)
                    if combat_power == 0 and 'Stats' in profile_detail:
                        for stat in profile_detail['Stats']:
                            if stat['Type'] == '공격력':
                                try:
                                    combat_power = int(stat['Value'].replace(',', ''))
                                except: pass
                                break
                
                char_data = char_basic.copy()
                char_data['CombatPower'] = combat_power
                enriched_data.append(char_data)
                
        # 3. 정렬 (전투력 높은 순)
        enriched_data.sort(key=lambda x: int(x.get('CombatPower', 0)), reverse=True)
        return enriched_data