import time
import json
import random
import urllib
import requests
from bs4 import BeautifulSoup


class Newhouse591Spider():
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.68',
            'device': 'pc',
            'deviceid': '1234567890',  # 好像可以隨意值，但不給取不到 "建案詳情 > 周邊機能"
        }

    def search(self, filter_params=None, sort_param=None, want_page=1):
        """ 搜尋新建案

        :param filter_params: 篩選參數
        :param sort_params: 排序參數
        :param want_page: 想要抓幾頁
        :return total_count: requests 建案總數
        :return house_list: requests 搜尋結果建案資料清單
        """
        total_count = 0
        house_list = []
        page = 0
        
        # 搜尋建案
        url = 'https://newhouse.591.com.tw/home/housing/list-search'
        params = 'device=pc&device_id=1234567890'
        
        # 篩選參數
        if filter_params:
            params += ''.join([f'&{key}={value}' for key, value, in filter_params.items()])
        # 排序參數
        if sort_param:
            params += ''.join([f'&{key}={value}' for key, value, in sort_param.items()])

        self.headers['referer'] = urllib.parse.quote(f'https://newhouse.591.com.tw/list?{params}')
        
        while page < want_page:
            page += 1
            params = f'page={page}&{params}'
            print(f"Get 建案資料: {url}")
            r = requests.get(url, params=params, headers=self.headers)
            if r.status_code != requests.codes.ok:
                print('請求失敗', r.status_code)
                break
            
            data = r.json()
            total_count = data['data']['total']
            house_list.extend(data['data']['items'])
            
            # 判斷是否為最後一頁
            if page >= data['data']['total_page']:
                break
            time.sleep(random.uniform(2, 6))  # 隨機 delay 一段時間

        return total_count, house_list

    def get_newhouse_detail(self, house_id):
        """ 取得建案詳情 (建案資料+周邊機能+實價登錄)

        :param house_id: 建案 ID
        :return house_detail: requests 建案詳細資料
        """
        house_detail = {}
        
        # 建案資料
        url = f'https://bff.591.com.tw/v1/housing/detail-info?id={house_id}&is_auth=0'
        self.headers['referer'] = 'https://newhouse.591.com.tw/'
        print(f"Get 建案資料: {url}")
        r = requests.get(url, headers=self.headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
        else:
            data = r.json()
            house_detail['detail'] = data['data']
                    
            with open('./_newhouse591_detail.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
        time.sleep(random.uniform(1, 3))  # 隨機 delay 一段時間
        
        # 周邊機能
        url = f'https://bff-newhouse.591.com.tw/v1/detail/surrounding?id={house_id}&is_auth=0'
        # https://bff-newhouse.591.com.tw/v1/detail/surrounding?id=120137&is_auth=0
        self.headers['referer'] = 'https://newhouse.591.com.tw/'
        print(f"Get 周邊機能: {url}")
        r = requests.get(url, headers=self.headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
        else:
            data = r.json()
            house_detail['surrounding'] = data['data']
            with open('./_newhouse591_surrounding.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
        time.sleep(random.uniform(1, 3))  # 隨機 delay 一段時間

        # 實價登錄
        # 要先取得 community_id
        url = f'https://newhouse.591.com.tw/{house_id}?roster_type=1'
        r = requests.get(url, headers=self.headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
        else:
            soup = BeautifulSoup(r.text, 'html.parser')
            canonical_href = soup.select_one('section.market a.status-table')['href']
            community_id = canonical_href.split("/control/")[-1].split("?")[0]
            
            # 抓取實價登錄清單
            price_list = []
            page = 0
            while page < 99:
                page += 1
                url = f'https://bff-market.591.com.tw/v1/price/list?community_id={community_id}&split_park=1&page={page}&page_size=20&_source=0'
                # https://bff-market.591.com.tw/v1/price/list?community_id=5935592&split_park=1&page=2&page_size=20&_source=0
                self.headers['referer'] = 'https://market.591.com.tw/'
                print(f"Get 實價登錄: {url}")
                r = requests.get(url, headers=self.headers)
                if r.status_code != requests.codes.ok:
                    print('請求失敗', r.status_code)
                    break
            
                data = r.json()
                price_list.extend(data['data']['items'])
                with open('./_newhouse591_price.json', 'w', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False, indent=4))
                
                # 判斷是否為最後一頁
                if page >= data['data']['total_page']:
                    break
                time.sleep(random.uniform(2, 5))  # 隨機 delay 一段時間
            
            house_detail['price'] = price_list
        
        return house_detail


if __name__ == "__main__":
    # 591房屋交易 新建案
    newhouse591_spider = Newhouse591Spider()
    
    # 篩選條件
    filter_params = {
        # 關鍵字
        'keyword': '花園',  # %E6%B0%B4%E6%BC%BE
        
        # 按地區
        'regionid': '1',  # (縣市) 台北
        # 'sectionid': '10',  # (地區) 台北 > 內湖區
        # 'shop_id': '164',  # (生活圈) 台北 > 內湖區 > 內湖科技園區
        
        # 按捷運 (有 regionid=1 參數，但應該沒影響)
        # 'search_type': '1',
        # 'city': '1',  # (捷運) 台北捷運
        # 'subway_line': '2',  # (路線) 台北捷運 > 淡水信義線
        # 'subway_id': '4198',  # (站點) 台北捷運 > 淡水信義線 > 新北投
        
        # 'unit_price': '1,2',  # (單價) 50萬/坪以下+50-70萬/坪
        # 'total_price': '3',  # (總價) 2000-3000萬
        # 'room': '4',  # (格局) 四房
        # 'shape': '3',  # (型態) 住宅大樓
        # 'build_type': '1',  # (狀態) 預售屋
        # 'purpose': '1',  # (用途) 住家用
        # 'tag': '1,4,5,10',  # (特色) 近捷運+重劃區+近公園+制震宅
    }
    # 排序依據 (只能選一個) (有時候加入排序反而會沒結果，使用網頁就會這樣了)
    sort_param = {
        # 'sort': '1',  # 金額排序從小到大
        # 'sort': '5',  # 瀏覽人數從多到少
    }
    
    # 範例條件查詢完整網址
    # https://newhouse.591.com.tw/list?regionid=1&sectionid=10&unit_price=1,2&build_type=1&purpose=1&shape=3
    # https://newhouse.591.com.tw/home/housing/list-search?page=1&device=pc&device_id=qdmsr4i65857aj9rttoqdrjg87&regionid=1&sectionid=10&unit_price=1,2&purpose=1&shape=3&build_type=1
    
    total_count, houses = newhouse591_spider.search(filter_params, sort_param, want_page=1)
    print('搜尋結果建案總數：', total_count)
    # with open('./newhouse591_search.json', 'w', encoding='utf-8') as f:
    #     f.write(json.dumps(houses, ensure_ascii=False, indent=4))
    #     print("新建案搜尋結果 已儲存至 ./newhouse591_search.json")

    # time.sleep(random.uniform(2, 5))  # 隨機 delay 一段時間
    house_detail = newhouse591_spider.get_newhouse_detail(houses[0]['hid'])
    # house_detail = newhouse591_spider.get_newhouse_detail('135743')  # 120137
    print(house_detail)
    # with open('./newhouse591_detail.json', 'w', encoding='utf-8') as f:
    #     f.write(json.dumps(house_detail, ensure_ascii=False, indent=4))
    #     print("建案詳情 已儲存至 ./newhouse591_detail.json")
