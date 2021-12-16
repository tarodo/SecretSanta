items = {
    'Носки': {
        1: {
            'name': 'Яркие фантазийные носки от St. Friday',
            'image': 'https://rostov.oimio.ru/wa-data/public/shop/products/63/85/18563/images/79999/79999.970.jpg',
            'price': '455',
        },
       2: {
            'name': 'Носки женские Conte Elegant',
            'image': 'https://chylok.ru/image/cache/data/products/025d7d48c5d2a6ed22abb89b5e16e50f2-800x1200.jpg',
            'price': '133',
        },
        3: {
            'name': 'Носки HOBBY "Я тебя Мур-мур"',
            'image': 'https://mensocks.ru/upload/iblock/6fe/6fe8429c7b7337b4ee7d38a86cc84744.jpg',
            'price': '350',
        }

    }
}


def get_items(category):
    return items[category]
