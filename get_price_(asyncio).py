import time
import asyncio
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


async def get_goods(last):
    loop = asyncio.get_event_loop()
    goods = []
    futures = [
        loop.run_in_executor(
            None,
            requests.get,
            'https://fix-price.ru/buyers/catalog/page-{}/'.format(page)
        )
        for page in range(last+1)
    ]
    for response in await asyncio.gather(*futures):
        goods += get_goods_from_page(response.text)
    return goods


async def add_info(goods):
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(
            None,
            requests.get,
            good['link']
        )
        for good in goods
    ]
    for position, response in enumerate(await asyncio.gather(*futures)):
        goods[position].update(get_good_info(response.text))
    return goods


if __name__ == '__main__':
    start_time = time.time()
    catalog_url = 'https://fix-price.ru/buyers/catalog/'
    catalog_response = requests.get(catalog_url)
    last_page = get_page_count(catalog_response.text)
    loop = asyncio.get_event_loop()
    all_goods = loop.run_until_complete(get_goods(last_page))
    print('All goods got. Time spent {}'.format(time.time() - start_time))
    start_time_info = time.time()
    all_goods_info = loop.run_until_complete(add_info(all_goods))
    print('All goods info got. Time spent {}'.format(
        time.time() - start_time_info
    ))
    print(all_goods_info)
    print('======= {} second ======='.format(time.time() - start_time))
