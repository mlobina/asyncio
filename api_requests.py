import aiohttp
import asyncio

from models import async_session, Person

SW_API = 'https://swapi.dev/api/people/'  # БД по Star Wars


async def get_page(url: str):
    """заходим на endpoint и получаем инф-цию в json"""

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response = await response.json()
        await session.close()
    return response


async def get_detail_names(json: dict, detail: str, key: str):  # пример 'films': ['https://swapi.dev/api/films/1/']
    """переходим на endpoints films, species, starships, vehicles и уточняем список их названий для героя"""

    detail_requests = [get_page(url) for url in json[detail]]
    results = await asyncio.gather(*detail_requests)
    names = [res[key] for res in results]
    return ', '.join(names)


async def get_homeworld(json: dict):  # пример 'homeworld': 'https://swapi.dev/api/planets/1/'
    """переходим на endpoints planet и уточняем  название homeworld для героя"""

    res = await get_page(json['homeworld'])
    return res['name']


async def main():
    session = async_session()

    people_tasks = [asyncio.create_task(get_page(f'{SW_API}{i}')) for i in range(100)]  # таски запросов по всем героям

    people = await asyncio.gather(*people_tasks)  # результат тасок  - список с  json по каждому герою

    for person in people:

        if person.get('detail') is None: # исключаем из обработки экземпляры {'detail': 'Not found'}
            detail_tasks = []

            films = asyncio.create_task(get_detail_names(person, 'films', 'title'))
            detail_tasks.append(films)

            homeworld = asyncio.create_task(get_homeworld(person))
            detail_tasks.append(homeworld)

            species = asyncio.create_task(get_detail_names(person, 'species', 'name'))
            detail_tasks.append(species)

            starships = asyncio.create_task(get_detail_names(person, 'starships', 'name'))
            detail_tasks.append(starships)

            vehicles = asyncio.create_task(get_detail_names(person, 'vehicles', 'name'))
            detail_tasks.append(vehicles)

            detail_res = await asyncio.gather(*detail_tasks)


            new_person = Person(pers_id=int(person['url'].split('/')[-2]),
                                birth_year=person['birth_year'],
                                eye_color=person['eye_color'],
                                films=detail_res[0],
                                gender=person['gender'],
                                hair_color=person['hair_color'],
                                height=person['height'],
                                homeworld=detail_res[1],
                                mass=person['mass'],
                                name=person['name'],
                                skin_color=person['skin_color'],
                                species=detail_res[2],
                                starships=detail_res[3],
                                vehicles=detail_res[4]
                                )

            session.add(new_person)
            await session.commit()


if __name__ == '__main__':
    asyncio.run(main())
