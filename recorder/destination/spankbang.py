import asyncio
import glob
import logging
import os.path
import pathlib
import time

import playwright.async_api

import recorder

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def upload(path, title):
    async with playwright.async_api.async_playwright() as p:
        browser = await p.chromium.launch_persistent_context('./spankbang_userdata', headless=False)
        page = await browser.new_page()

        auth_url = 'https://spankbang.com/users/auth'
        await page.goto(auth_url)

        if auth_url == page.url:
            # login
            logging.info('logging in')
            try:
                await page.locator('//*[@id="age_check_yes"]').click(timeout=2 * 1000)
            except playwright.async_api.TimeoutError:
                pass
            await page.locator('//*[@id="auth_register_form"]/ul/li[1]/a').click()
            await page.locator('//*[@id="log_username"]').fill(recorder.config['spankbang']['username'])
            await page.locator('//*[@id="log_password"]').fill(recorder.config['spankbang']['password'])
            await page.locator('//*[@id="auth_login_form"]/p[1]/button').click()

        # goto upload
        logging.info('goto upload page')
        await page.locator('//*[@id="body-html"]/header/nav/ul/li[1]/a').click()
        file_input = page.locator('//*[@id="fileInput"]')
        await file_input.wait_for(timeout=10 * 1000, state='visible')
        logging.info('file input found')
        await page.locator('//*[@id="fileInput"]').set_input_files(path)

        # wait until upload finished
        while not await page.locator('//*[@id="upload"]/div/div[3]/p').is_visible():
            progress = await page.locator('//*[@id="form-container-anchor"]/div[5]/div[2]').inner_text()
            est = await page.locator('//*[@id="form-container-anchor"]/div[6]/span[1]').inner_text()
            speed = await page.locator('//*[@id="form-container-anchor"]/div[6]/span[2]').inner_text()
            print(f'\rProgress: {progress}, est: {est}, speed: {speed}', end='', flush=True)

        # fill in video info
        # title
        await page.locator('//*[@id="name_inp"]').fill(title)
        # tags
        tags_input = page.locator('//*[@id="tag_inp"]/div/input')
        await tags_input.type('Korean')
        await page.wait_for_timeout(1000)
        await tags_input.press('Enter')
        await tags_input.type('Korean')
        await page.wait_for_timeout(1000)
        await tags_input.press('Enter')
        # categories
        await page.locator('//*[@id="category_list"]/label[3]').click()  # Asian
        await page.locator('//*[@id="category_list"]/label[13]').click()  # Cam

        # submit
        await page.locator('//*[@id="upload_form_button"]').click()

        i = 0
        while page.url != 'https://spankbang.com/users/videos':
            await page.wait_for_timeout(1000)
            i += 1

            assert i < 16, 'upload failed'

        await page.close()


async def main():
    files = glob.glob(r'Y:\videos\record\panda\**\*.mp4', recursive=True)
    upload_files = []

    for file in files:
        # check if recently modified
        if os.path.getmtime(file) > time.time() - 10:
            logging.info(f'{file} is busy, skip')
            continue

        path = pathlib.Path(file)
        title = f'pandalive_{path.parent.name}_{path.stem}'
        upload_files.append((file, title))

    logging.info(f'uploading {len(upload_files)} files')
    logging.info(upload_files)

    for path, title in upload_files:
        filesize = os.path.getsize(path)

        if filesize < 1024 * 1024 * 64:
            logging.info(f'{path} < 64MB, skip')
            continue

        logging.info(f'uploading {path} with title {title}')

        try:
            await upload(path, title)
        except AssertionError as e:
            logging.error(f'upload failed: {e}')

        dst_path = path.replace(f'{os.sep}record{os.sep}', f'{os.sep}validate{os.sep}')
        pathlib.Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        os.rename(path, dst_path)
        logging.info(f'uploaded {path} -> {dst_path}')


if __name__ == '__main__':
    asyncio.run(main())
