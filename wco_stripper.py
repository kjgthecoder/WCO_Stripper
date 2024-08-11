from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from requests.exceptions import ChunkedEncodingError, HTTPError, RequestException 
import os 
import time
from urllib.parse import urlparse

def process_video_title(episode_title): 
    invalid_chars = set(r'\/:*?"<>| ')
    return ''.join(char for char in episode_title if char not in invalid_chars)

def get_episode_title_and_links(driver, anime_url): 
    epidsodes_list = [] 
    driver.get(anime_url)
    series_title = process_video_title(driver.title.rstrip(' - Watch English Dubbed Anime Online now'))
    os.makedirs(series_title, exist_ok=True)  
    print(driver.title)

    episodes = driver.find_elements(By.CLASS_NAME, 'cat-eps')
    episodes = reversed(episodes)

    for epidsode in episodes:
        episode_link = epidsode.find_element(By.TAG_NAME, 'a')
        video_title = (process_video_title(episode_link.text)) + '.mp4'
        episode_href = episode_link.get_attribute('href')
        episode_info = {'video_title': video_title, 'episode_href': episode_href}
        epidsodes_list.append(episode_info)

    return epidsodes_list, series_title

def download_episdoes(driver, series_title, episodes, anime_url):
    for epidsode in episodes: 
        print(f'Beginning to download {epidsode["video_title"]}')
        driver.get(epidsode['episode_href'])
        wait = WebDriverWait(driver, 10)

        print(driver.title) 


        # driver.switch_to.frame('cizgi-js-0')
        frame = wait.until(EC.frame_to_be_available_and_switch_to_it('cizgi-js-0'))
        print(f"Switched to frame: {driver.title}")


        # Find Video Tag 
        # video_element = driver.find_element(By.TAG_NAME, 'video')
        # Correct usage of lambda to wait for the video element to have a 'src' attribute
        video_element = wait.until(lambda driver: driver.find_element(By.TAG_NAME, 'video') if driver.find_element(By.TAG_NAME, 'video').get_attribute('src') else False)
        print("Video element with src is visible.")

        # Check if video tag was found and print its attributes
        if video_element:
            src = video_element.get_attribute('src') 
            print(f'src is: {src}')
            # Execute JavaScript to retrieve all attributes of the element.
            attributes = driver.execute_script("""
                var items = {}; 
                for (index = 0; index < arguments[0].attributes.length; ++index) { 
                    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value 
                } 
            return items;
            """, video_element)
            # Print all attributes.
            print(attributes)

            if not src: 
                print("No src was found.") 
            # print(f'going to {src}')
            driver.get(src)
            print(f"Current URL: {driver.current_url}")
            
            vid_src = driver.current_url
            video_path = f"./{series_title}/{epidsode['video_title']}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
                'Accept-Language': 'en-US,en;q=0.5', 
                # 'Range': 'bytes=24608533-', 
                'Connection': 'keep-alive', 
                'Referer': vid_src,   # Adjust as necessary to the URL of the page hosting the iframe
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
                'Accept-Encoding': 'identity'
            }

            attempt = 0 
            retries = 5
            while attempt < retries: 
                try: 
                    print("Beginning download to directory.")
                    with requests.get(vid_src, headers=headers, stream=True, timeout=30) as response: 
                        response.raise_for_status() # Raises HTTPError for bad response 
                        with open(video_path, 'wb') as file: 
                            for chunk in response.iter_content(chunk_size=8192): 
                                if chunk: 
                                    file.write(chunk) 
                    print("Download sucessful.")
                    break
                except (ChunkedEncodingError, HTTPError) as e: 
                    print(f'Error: {e}, retyring...')
                    print(f"Attempt {attempt+1}/{retries}")
                    attempt += 1
                    parsed_url = urlparse(vid_src)
                    domain = parsed_url.netloc
                    print(f'domain is: {domain}')
                    headers = { 
                        'Host': domain, 
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0', 
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 
                        'Accept-Language': 'en-US,en;q=0.5', 
                        'Accept-Encoding': 'gzip, deflate, br', 
                        'Connection': 'keep-alive', 
                        'Upgrade-Insecure-Requests': '1', 
                        'Sec-Fetch-Dest': 'document', 
                        'Sec-Fetch-Mode': 'navigate', 
                        'Sec-Fetch-Site': 'cross-site'
                    }
                    # time.sleep(5)
                    time.sleep(2 ** attempt) # Exponential backoff
                except RequestException as e: 
                    print(f'Request failed: {e}')
                    break 

            if attempt == retries: 
                with open('failed_eps.txt', 'a') as file: 
                    file.write(f'{video_path} failed to download.')

            driver.get(anime_url) 

def main(anime_url): 
    # Initialize WebDriver 
    options = webdriver.FirefoxOptions() 
    driver = webdriver.Firefox(options=options) 

    episodes_list, series_title = get_episode_title_and_links(driver, anime_url)
    for episode in episodes_list: 
        print(episode)
    print(f'Downloading Every Episdoe of {series_title} now.')

    download_episdoes(driver, series_title, episodes_list, anime_url)

    driver.quit() 

if __name__ == '__main__':
    main('https://www.wcoanimedub.tv/anime/haikyuu')
    print('Series downloaded successfully.')


