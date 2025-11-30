# -*- coding: utf-8 -*-
from flask import Flask, request, render_template_string
import requests
from datetime import datetime, date
import os

try:
    from lunardate import LunarDate  # pip install lunardate
except ImportError:
    LunarDate = None

app = Flask(__name__)

# ===================== 這裡填你的 OpenWeatherMap API KEY =====================
# 請先到 https://openweathermap.org/ 申請帳號並建立 API key
API_KEY = "5f8a276578f278e7b8df6f8989f14351"
# ======================================================================

# 12 生肖 (可給使用者選)
ZODIACS = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]

# 每個生肖的基本幸運色（示意，可自行調整）
LUCKY_COLOR_RULES = {
    "鼠": ["藍色", "金色", "黑色"],
    "牛": ["綠色", "黃色", "棕色"],
    "虎": ["橙色", "白色", "藍色"],
    "兔": ["粉紅色", "綠色", "紫色"],
    "龍": ["金色", "紅色", "紫色"],
    "蛇": ["紫色", "黑色", "銀色"],
    "馬": ["紅色", "橙色", "棕色"],
    "羊": ["米色", "綠色", "粉紅色"],
    "猴": ["金色", "藍色", "白色"],
    "雞": ["黃色", "金色", "橙色"],
    "狗": ["咖啡色", "紅色", "藍色"],
    "豬": ["粉紅色", "灰色", "黑色"],
}

# 依氣溫給一個大致的穿搭層次建議
def get_layer_suggestion(temp_c: float) -> str:
    if temp_c >= 30:
        return "超熱：建議輕薄短袖、透氣材質，減少層次以免中暑。"
    elif 25 <= temp_c < 30:
        return "溫暖：短袖或薄長袖即可，外出可備一件薄外套。"
    elif 20 <= temp_c < 25:
        return "舒適微涼：薄長袖＋薄外套，或洋裝搭配輕外罩。"
    elif 15 <= temp_c < 20:
        return "偏涼：長袖上衣＋薄針織或西裝外套，下身長褲或長裙。"
    elif 10 <= temp_c < 15:
        return "冷：建議毛衣＋大衣或防風外套，注意脖子與腳部保暖。"
    else:
        return "很冷：多層次穿搭（發熱衣＋毛衣＋厚外套），必要時加圍巾、手套與帽子。"

# 取得今天農曆日期（如果沒有安裝 lunardate，會用簡單字串代替）
def get_current_lunar_day():
    today = date.today()
    if LunarDate is None:
        # 後備方案：只顯示西元日期
        lunar_str = f"（未安裝 lunardate，顯示西元）{today.year}-{today.month}-{today.day}"
        # 用 day 當作運算用數字
        return lunar_str, today.day

    lunar = LunarDate.fromSolarDate(today.year, today.month, today.day)
    lunar_str = f"農曆 {lunar.year} 年 {lunar.month} 月 {lunar.day} 日"
    return lunar_str, lunar.day

# 計算生肖的今日幸運色
def calculate_lucky_color(zodiac: str, day_num: int) -> str:
    colors = LUCKY_COLOR_RULES.get(zodiac)
    if not colors:
        # 不在列表裡就給一個通用顏色
        return "白色"
    # 用農曆日期做簡單輪替
    idx = (day_num - 1) % len(colors)
    return colors[idx]

# 取得城市當前氣溫與描述（使用 OpenWeatherMap）
def get_current_temperature(city: str, api_key: str):
    if not api_key or "在這裡填入" in api_key:
        return None, "尚未設定 OpenWeatherMap API Key"

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "zh_tw",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return temp, desc
    except Exception as e:
        print("取得天氣發生錯誤：", e)
        return None, f"無法取得天氣資訊，請確認城市名稱是否正確，或稍後再試。"

# 綜合生肖、幸運色與天氣給出穿搭建議
def recommend_outfit(temperature, lucky_color: str, weather_desc: str, city: str):
    if temperature is None:
        return {
            "error": "無法取得天氣資訊，所以目前沒辦法提供完整穿搭建議。"
        }

    layer_suggestion = get_layer_suggestion(temperature)

    # 根據天氣描述給一些小提醒
    weather_tips = []
    low_desc = (weather_desc or "").lower()
    if "rain" in low_desc or "雨" in weather_desc:
        weather_tips.append("記得攜帶雨具（雨衣或雨傘），鞋子可選擇防水材質。")
    if "cloud" in low_desc or "陰" in weather_desc:
        weather_tips.append("天氣較陰，可以在造型中加入亮色單品提振精神。")
    if "clear" in low_desc or "晴" in weather_desc:
        weather_tips.append("陽光較強時，建議搭配帽子或墨鏡，並使用防曬。")
    if "wind" in low_desc or "風" in weather_desc:
        weather_tips.append("風比較大，可選擇防風外套，避免穿過於飄逸的裙擺。")

    # 顏色應用建議
    color_tip = f"今日幸運色為 <b>{lucky_color}</b>，可以作為上衣、褲子、外套或配件的主色，增加整體好運氣 ✨"

    # 穿搭主題（簡單根據溫度）
    if temperature >= 28:
        theme = f"清爽輕盈的 {lucky_color} 夏日造型"
    elif temperature >= 18:
        theme = f"日常舒適的 {lucky_color} 休閒穿搭"
    elif temperature >= 10:
        theme = f"溫暖質感的 {lucky_color} 秋冬風格"
    else:
        theme = f"高保暖的 {lucky_color} 冬季禦寒造型"

    # 具體穿搭建議（示意，可以依你原本邏輯再調整）
    tips = []

    # 上身建議
    if temperature >= 25:
        tips.append(f"上身可以選擇{lucky_color}系短袖 T-shirt 或襯衫，材質以棉、亞麻等透氣為主。")
    elif temperature >= 18:
        tips.append(f"上身可以搭配{lucky_color}薄長袖或襯衫，外層加一件輕薄外套或罩衫。")
    elif temperature >= 10:
        tips.append(f"上身建議發熱衣或長袖上衣打底，再搭配{lucky_color}毛衣或針織衫。")
    else:
        tips.append(f"上身可採用多層次搭配：發熱衣＋毛衣＋{lucky_color}厚外套，確保保暖。")

    # 下身建議
    if temperature >= 22:
        tips.append("下身可以選擇輕薄長褲、九分褲或裙裝，若需要通勤可搭配舒適運動鞋。")
    else:
        tips.append("下身建議長褲或厚裙搭配刷毛褲襪，避免腿部受寒。")

    # 配件顏色運用
    tips.append(f"可以用{lucky_color}作為包包、鞋子、圍巾或髮飾的顏色，增加造型重點與好運元素。")

    # 加上天氣提醒
    tips.extend(weather_tips)

    return {
        "城市": city,
        "當前溫度": f"{temperature:.1f} °C",
        "天氣狀況": weather_desc,
        "穿搭主題": theme,
        "建議層次": layer_suggestion,
        "顏色建議": color_tip,
        "搭配建議": tips,
    }

# -------------------------- HTML 模板（放在程式裡） --------------------------
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <title>生肖幸運色穿搭推薦</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 24px;
      background: #f5f5f5;
    }
    h1 {
      text-align: center;
      margin-bottom: 24px;
    }
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
      margin-bottom: 20px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
    }
    select, input[type="text"] {
      width: 100%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #ccc;
      margin-bottom: 16px;
      font-size: 14px;
    }
    button {
      padding: 10px 18px;
      border-radius: 999px;
      border: none;
      cursor: pointer;
      font-weight: 600;
      background: #222;
      color: #fff;
      font-size: 14px;
    }
    button:hover {
      opacity: .9;
    }
    .error {
      color: #b00020;
      margin-bottom: 12px;
      font-weight: 600;
    }
    ul {
      padding-left: 20px;
    }
    .footer {
      text-align: center;
      font-size: 12px;
      color: #777;
      margin-top: 16px;
    }
  </style>
</head>
<body>
  <h1>🐉 生肖 & 農曆 幸運色穿搭推薦</h1>

  <div class="card">
    <form method="post">
      {% if error %}
        <div class="error">{{ error }}</div>
      {% endif %}

      {% if api_key_not_set %}
        <div class="error">⚠️ 尚未設定 OpenWeatherMap API Key，無法取得即時天氣，請先修改程式中的 <code>API_KEY</code>。</div>
      {% endif %}

      <label for="zodiac">您的生肖</label>
      <select id="zodiac" name="zodiac" required>
        <option value="">請選擇</option>
        {% for z in zodiacs %}
          <option value="{{ z }}" {% if form_zodiac == z %}selected{% endif %}>
            {{ z }}
          </option>
        {% endfor %}
      </select>

      <label for="city">想查詢的城市（英文，如：Taipei, Tokyo, London）</label>
      <input
        id="city"
        type="text"
        name="city"
        placeholder="例如：Taipei"
        required
        value="{{ form_city }}"
      />

      <button type="submit">生成今天的穿搭建議 ✨</button>
    </form>
  </div>

  {% if result %}
    <div class="card">
      <h2>⭐ 今日運勢概要</h2>
      <p>📅 今日農曆：{{ result.lunar_day }}</p>
      <p>🧧 您的生肖：{{ result.zodiac }}</p>
      <p>🎨 幸運色：<b>{{ result.lucky_color }}</b></p>
      <p>{{ result.color_tip | safe }}</p>
    </div>

    <div class="card">
      <h2>👗 穿搭建議</h2>
      <p>📍 城市：{{ result.city }}</p>
      <p>🌡️ 氣溫：{{ result.temperature }}（{{ result.weather_desc }}）</p>
      <p>✨ 穿搭主題：{{ result.theme }}</p>
      <p>🧥 建議保暖層次：{{ result.layer }}</p>

      {% if result.tips %}
        <h3>📋 具體建議：</h3>
        <ul>
          {% for t in result.tips %}
            {% if t %}
              <li>{{ t | safe }}</li>
            {% endif %}
          {% endfor %}
        </ul>
      {% endif %}
    </div>
  {% endif %}

  <div class="footer">
    <p>現在時間：{{ now_str }}</p>
  </div>
</body>
</html>
"""

# --------------------------- Flask 路由 ---------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    form_zodiac = ""
    form_city = ""

    if request.method == "POST":
        form_zodiac = (request.form.get("zodiac") or "").strip()
        form_city = (request.form.get("city") or "").strip()

        if not form_zodiac:
            error = "請選擇您的生肖。"
        elif not form_city:
            error = "請輸入城市名稱。"
        else:
            # 1. 農曆日期
            lunar_day_str, day_num = get_current_lunar_day()

            # 2. 幸運色
            lucky_color = calculate_lucky_color(form_zodiac, day_num)

            # 3. 天氣資訊
            temp, weather_desc = get_current_temperature(form_city, API_KEY)

            # 4. 穿搭建議
            rec = recommend_outfit(temp, lucky_color, weather_desc, form_city)

            if "error" in rec:
                error = rec["error"]
            else:
                result = {
                    "zodiac": form_zodiac,
                    "lunar_day": lunar_day_str,
                    "lucky_color": lucky_color,
                    "city": rec["城市"],
                    "temperature": rec["當前溫度"],
                    "weather_desc": rec["天氣狀況"],
                    "theme": rec["穿搭主題"],
                    "layer": rec["建議層次"],
                    "color_tip": rec["顏色建議"],
                    "tips": rec.get("搭配建議", []),
                }

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    api_key_not_set = (not API_KEY) or ("在這裡填入" in API_KEY)

    return render_template_string(
        HTML_TEMPLATE,
        zodiacs=ZODIACS,
        result=result,
        error=error,
        form_zodiac=form_zodiac,
        form_city=form_city,
        now_str=now_str,
        api_key_not_set=api_key_not_set,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

