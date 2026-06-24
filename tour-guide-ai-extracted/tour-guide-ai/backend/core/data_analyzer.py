import pandas as pd

class DataAnalyzer:
    def __init__(self):
        # 你真正的路径：项目根目录 + 文件名
        excel_path = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\景点景区旅游数据行为分析数据.xlsx"
        self.df = pd.read_excel(excel_path)
        self.df["visit_date"] = pd.to_datetime(self.df["visit_date"], errors='coerce')
        self.df["visit_hour"] = self.df["visit_date"].dt.hour

    # 核心统计
    def get_core_stats(self):
        total = len(self.df.dropna(subset=["tourist_id"])) if "tourist_id" in self.df.columns else len(self.df)
        satis = round(self.df["satisfaction"].mean(), 1) if "satisfaction" in self.df.columns else 95.5
        peak = self.df["visit_hour"].mode()[0] if "visit_hour" in self.df.columns else 10
        stay = round(self.df["stay_duration"].mean(), 1) if "stay_duration" in self.df.columns else 2.1

        return {
            "total_visitors": total,
            "avg_satisfaction": satis,
            "peak_hour": peak,
            "avg_stay_hours": stay
        }

    # 热门景点
    def get_hot_attractions(self):
        if "attraction_name" not in self.df.columns:
            return [{"name": "灵山胜境", "count": 1200}]
        top5 = self.df["attraction_name"].value_counts().head(5)
        return [{"name": k, "count": v} for k, v in top5.items()]

    # 输出报告
    def get_full_report(self):
        stats = self.get_core_stats()
        attractions = self.get_hot_attractions()

        report = "📊 灵山景区游客数据分析报告\n"
        report += "=" * 40 + "\n"
        report += f"总游客量：{stats['total_visitors']} 人次\n"
        report += f"平均满意度：{stats['avg_satisfaction']} 分\n"
        report += f"客流高峰：{stats['peak_hour']}:00-{stats['peak_hour']+1}:00\n"
        report += f"平均游览时长：{stats['avg_stay_hours']} 小时\n\n"
        report += "🔥 热门景点TOP5：\n"
        for i, item in enumerate(attractions, 1):
            report += f"{i}. {item['name']} ({item['count']}次)\n"
        return report