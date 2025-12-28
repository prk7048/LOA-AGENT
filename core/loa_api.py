import requests
import os

class LostArkAPI:
    """
    로스트아크 API와 통신하는 클래스
    """
    def __init__(self):
        self.api_key = os.getenv("LOA_API_KEY")
        self.base_url = "https://developer-lostark.game.onstove.com"
        self.headers = {
            "accept" : "appllication/json",
            "authorization": f"bearer {self.api_key}"
        }

    def get_character_profile(self, character_name):
        """
        캐릭터 이름으로 캐릭터 정보 조회
        """
        # 1. URL 만들기 (API 문서 기준: /armories/characters/{characterName}/profiles)
        # URL 인코딩은 requests가 알아서 해줍니다.
        url = f"{self.base_url}/armories/characters/{character_name}/profiles"

        try:
            # 2. GET 요청 만들기
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()

                if data is None:
                    return None
                
                # 4. DB 컬럼 이름에 맞춰서 데이터 가공 (Mapping)
                # API가 주는 키 값 : CharacterName, ServerName, CharacterClassName, ItemAvgLevel                
                parsed_data = {
                    "CharacterName": data['CharacterName'],
                    "ServerName": data['ServerName'],
                    "CharacterClassName": data['CharacterClassName'],
                    "ItemAvgLevel": float(data['ItemAvgLevel'].replace(",", "")), # "1,680.00" -> 1680.0 변환
                    "CombatPower": float(data['Stats'][0]['Value']) if 'Stats' in data else 0 # 공격력 예시
                }
                return parsed_data
            
            else:
                print ("API 요청 실패 : {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            print(f"통신 에러 {e}")
            return None
        