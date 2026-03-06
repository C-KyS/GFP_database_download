import os
import re
import ssl
import time
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置信息
BASE_URL = "https://data.jic.ac.uk/Gfp/"
SEARCH_URL = BASE_URL + "default.asp?Submit=SEARCH&GFPCloneID=&GeneID=&Putative+Function=&cytoplasm=&nucleus=&nucleolus=&cell+wall=&subcytoplasmic+compartments=&SR={sr}"

# 创建存储目录
os.makedirs("Green_Images", exist_ok=True)
os.makedirs("Gray_Images", exist_ok=True)


# 自定义TLS适配器（该网站HTTPS需要降低安全等级才能连接）
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def create_session():
    """创建带有TLS适配器和重试机制的Session"""
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.mount('https://', TLSAdapter(max_retries=retry))
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session


def solve_captcha(session):
    """自动解决网站的反机器人验证（提取序列中的偶数数字）"""
    r = session.get(BASE_URL + 'default.asp', timeout=30, verify=False)
    m = re.search(r'sequence:\s*(\d+)', r.text)
    if not m:
        # 没有验证码，可能已经通过
        return True
    seq = m.group(1)
    even_digits = ''.join(d for d in seq if int(d) % 2 == 0)
    print(f"正在解决验证码: {seq} -> {even_digits}")
    r2 = session.get(BASE_URL + 'default.asp', params={'validate': even_digits}, timeout=30, verify=False)
    if 'robot' in r2.text:
        print("验证码解决失败！")
        return False
    print("验证码通过！")
    return True


def download_file(session, url, folder, filename):
    if not url:
        return
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        print(f"已跳过(已存在): {filename}")
        return
    try:
        r = session.get(url, stream=True, timeout=30, verify=False)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"已保存: {filename}")
    except Exception as e:
        print(f"下载失败 {url}: {e}")


def main():
    session = create_session()

    # 第1步：解决反机器人验证
    print("正在连接网站，请稍候...")
    if not solve_captcha(session):
        print("无法通过验证，程序退出。")
        return

    # 第2步：遍历所有分页，收集详情页链接
    all_detail_ids = []
    sr = 0
    while True:
        url = SEARCH_URL.format(sr=sr)
        try:
            time.sleep(1)  # 请求间隔，避免服务器拒绝
            r = session.get(url, timeout=60, verify=False)
        except Exception as e:
            print(f"获取第{sr+1}页失败: {e}")
            break

        soup = BeautifulSoup(r.text, 'html.parser')

        # 检查是否被重新要求验证
        if 'robot' in r.text:
            print("需要重新验证...")
            if not solve_captcha(session):
                break
            continue

        detail_links = soup.find_all('a', href=lambda x: x and 'detail.asp?ID=' in x)
        if not detail_links:
            break

        for link in detail_links:
            href = link['href']
            # 提取ID（如 detail.asp?ID=U09002 -> U09002）
            id_match = re.search(r'ID=([^&]+)', href)
            if id_match:
                all_detail_ids.append(id_match.group(1))

        print(f"第{sr+1}页: 找到 {len(detail_links)} 条记录")
        sr += 1

    print(f"\n共找到 {len(all_detail_ids)} 组数据，开始下载图片...")

    # 第3步：访问每个详情页，下载图片
    for i, detail_id in enumerate(all_detail_ids, 1):
        detail_url = BASE_URL + f"detail.asp?ID={detail_id}"

        try:
            time.sleep(0.5)  # 请求间隔
            res = session.get(detail_url, timeout=60, verify=False)
            soup_detail = BeautifulSoup(res.text, 'html.parser')

            # 提取GFP Clone ID作为文件名
            clone_id = detail_id
            rows = soup_detail.find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 2 and 'GFP Clone ID' in tds[0].text:
                    clone_id = tds[1].text.strip()
                    break

            # 查找图片（格式: /gfp/Largeimages/xxx-g.jpg 和 xxx-t.jpg）
            imgs = soup_detail.find_all('img', src=lambda x: x and 'images/' in x.lower())

            for img in imgs:
                img_url = urljoin(BASE_URL, img['src'])
                src = img['src'].lower()
                if '-g.jpg' in src or 'g.jpg' in src:
                    download_file(session, img_url, "Green_Images", f"{clone_id}_green.jpg")
                elif '-t.jpg' in src or 't.jpg' in src:
                    download_file(session, img_url, "Gray_Images", f"{clone_id}_gray.jpg")

            print(f"[{i}/{len(all_detail_ids)}] 处理完成: {clone_id}")

        except Exception as e:
            print(f"[{i}/{len(all_detail_ids)}] 解析详情页 {detail_id} 出错: {e}")

    print("\n全部完成！")


if __name__ == "__main__":
    main()