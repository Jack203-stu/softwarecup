import json
import os

class RouteRecommender:
    def __init__(self):
        # 只做一件事：读取景点数据
        data_path = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\data\spots.json"
        with open(data_path, "r", encoding="utf-8") as f:
            self.spots = json.load(f)

    # 直接返回所有景点数据，让AI自己规划路线
    def get_all_spots(self):
        return self.spots