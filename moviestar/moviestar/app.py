import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbsparta


# HTML 화면 보여주기
@app.route('/')
def home():
    return render_template('index.html')


# API 역할을 하는 부분
@app.route('/api/list', methods=['GET'])
def show_stars():
    # 1. db에서 mystar 목록 전체를 검색합니다. ID는 제외하고 like 가 많은 순으로 정렬합니다.
    # 참고) find({},{'_id':False}), sort()를 활용하면 굿!
    star_list = list(db.mystar.find({}, {'_id': False}).sort("like", -1))
    # 2. 성공하면 success 메시지와 함께 stars_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success', 'msg': star_list})


@app.route('/api/like', methods=['POST'])
def like_star():
    # 1. 클라이언트가 전달한 name_give를 name_receive 변수에 넣습니다.
    name_receive = request.form['name_give']
    print(name_receive)
    # 2. mystar 목록에서 find_one으로 name이 name_receive와 일치하는 star를 찾습니다.
    star = db.mystar.find_one({'name': name_receive})
    # print(star)
    # 3. star의 like 에 1을 더해준 new_like 변수를 만듭니다.
    new_like = star['like'] + 1

    # 4. mystar 목록에서 name이 name_receive인 문서의 like 를 new_like로 변경합니다.
    # 참고: '$set' 활용하기!
    db.mystar.update_one({'name': name_receive}, {'$set': {'like': new_like}})

    # 5. 성공하면 success 메시지를 반환합니다.
    return jsonify({'result': 'success', 'msg': 'like 연결되었습니다!'})


@app.route('/api/delete', methods=['POST'])
def delete_star():
    # 1. 클라이언트가 전달한 name_give를 name_receive 변수에 넣습니다.
    name_receive = request.form['name_give']
    # 2. mystar 목록에서 delete_one으로 name이 name_receive와 일치하는 star를 제거합니다.
    db.mystar.delete_one({'name': name_receive})
    # 3. 성공하면 success 메시지를 반환합니다.
    return jsonify({'result': 'success', 'msg': 'delete 연결되었습니다!'})


@app.route('/api/add', methods=['POST'])
def get_info():
    star_receive = request.form['star_give']
    search_url = "https://search.naver.com/search.naver?sm=top_hty&fbm=0&ie=utf8&query=" + star_receive

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    name = soup.select_one('#people_info_z > div.cont_noline > div > dl > dd.name > a > strong').text
    img_url = soup.select_one('#people_info_z > div.cont_noline > div > div > a:nth-child(1) > img')['src']
    recent_work = soup.select_one('#tx_ca_people_movie_content > ul > li:nth-child(1) > dl > dd:nth-child(1) > a').text

    doc = {
        'name': name,
        'img_url': img_url,
        'recent': recent_work,
        'url': search_url,
        'like': 0
    }

    count = db.mystar.count({'name': star_receive})
    if count == 0:
        db.mystar.insert_one(doc)
        return jsonify({'result': 'success', 'msg': 'add 연결되었습니다!'})
    elif count > 0:
        return jsonify({'result': 'fail', 'msg': '중복 데이터'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
