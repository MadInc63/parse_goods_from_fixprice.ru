import time
from threading import Thread, RLock
import requests
from bs4 import BeautifulSoup


def get_page_count(html_raw):
    soup = BeautifulSoup(html_raw, 'html.parser')
    return int(soup.find(
        'ul',
        {'class': 'list-pager list-pager-bottom'}
    ).find_all('li')[-1].text)


def get_goods_from_page(html_raw):
    goods_on_page = []
    soup = BeautifulSoup(html_raw, 'html.parser')
    catalog_tags = soup.find('div', {'class': 'box-catalog'})
    good_tags = catalog_tags.find_all('h6')
    for good_tag in good_tags:
        title = good_tag.a.text.strip()
        link = 'https://fix-price.ru' + good_tag.a.get('href')
        goods_on_page.append({
            'title': title,
            'link': link
        })
    return goods_on_page


def get_good_info(html_raw):
    soup = BeautifulSoup(html_raw, 'html.parser')
    description = soup.find('div', {'class': 'description'})
    price_per_set = soup.find('div', {'class': 'komplect_price'})
    article = soup.find('div', {'class': 'mid_rate'}).span.text
    price = soup.find('em', {'class': 'price_label'}).text.replace('руб', '')
    if description:
        if description.find('p'):
            description = description.p.text.strip()
        elif description.find('div'):
            description = description.div.span.text.strip()
    else:
        description = 'No description'
    if price_per_set:
        number_in_set = price_per_set.span.b.text
        price_per_set = price_per_set.span.em.text
        return {
            'article': article,
            'description': description,
            'price': price,
            'number_in_set': number_in_set,
            'price_per_set': price_per_set
        }
    else:
        return {
            'article': article,
            'description': description,
            'price': price,
        }


def thread_get_goods_info(url):
    global all_goods
    response = session.get(url)
    goods = get_goods_from_page(response.text)
    for good in goods:
        response = session.get(good['link'])
        info = get_good_info(response.text)
        good.update(info)
    lock.acquire()
    try:
        all_goods += goods
    finally:
        lock.release()


if __name__ == '__main__':
    start_time = time.time()
    session = requests.Session()
    session.headers.update = ({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/64.0.3282.140 Safari/537.36',
        'Accept-Language': 'ru,en;q=0.9'
    })
    catalog_url = 'https://fix-price.ru/buyers/catalog/'
    catalog_response = session.get(catalog_url)
    last_page = get_page_count(catalog_response.text)
    all_goods = []
    threads_list = []
    lock = RLock()
    for page in range(1, last_page+1):
        page_url = 'https://fix-price.ru/buyers/catalog/page-{}/'.format(page)
        thread = Thread(
            target=thread_get_goods_info,
            args=(page_url,)
        )
        thread.start()
        threads_list.append(thread)
        time.sleep(0.01)
    for thread in threads_list:
        thread.join()
    print('All goods got. Time spent {}'.format(time.time() - start_time))
    print(all_goods)
    print(len(all_goods))
