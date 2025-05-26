from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt


def get_html_with_selenium(url, wait_for_class="dx-data-row", timeout=30):  # timeout for selenium
    """
    Uses Selenium with geckodriver (Firefox) to open a URL,
    wait for dynamic content to load, and returns the page source.
    """
    print("Initializing Firefox WebDriver (geckodriver)...")

    firefox_options = FirefoxOptions()
    try:
        driver = webdriver.Firefox(options=firefox_options)
    except Exception:
        print(f"Error initializing Firefox WebDriver. Ensure geckodriver is in your PATH or specify its path.")
        return None

    print(f"Fetching URL: {url}")
    try:
        driver.get(url)

    except Exception as e:
        print(f"Error navigating to URL {url}: {e}")
        driver.quit()
        return None

    print(f"Waiting up to {timeout} seconds for elements with class '{wait_for_class}' to load...")
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, wait_for_class))
        )
        print("Dynamic content (elements with specified class) loaded.")
    except TimeoutException:
        print(f"Timed out waiting for dynamic content (class: {wait_for_class}) to load.")
        print("The page might not have the expected elements, or the wait time is too short.")
        print("Attempting to get page source anyway...")
    except Exception as e:
        print(f"An error occurred during WebDriver wait: {e}")
        driver.quit()
        return None

    rendered_html = driver.page_source
    driver.quit()
    print("WebDriver closed.")
    return rendered_html


def parse_rendered_nordpool_html(rendered_html_content):
    """
    Parses the rendered HTML content of the Nord Pool page to extract hourly prices.
    Assumes 'rendered_html_content' is the HTML string obtained after JavaScript execution (e.g., via Selenium).
    """
    if not rendered_html_content:
        print("No HTML content provided to parse.")
        return None

    print("Parsing HTML content with BeautifulSoup...")
    soup = BeautifulSoup(rendered_html_content, 'html.parser')

    hourly_prices_data = []

    datagrid_content_div = soup.find('div', class_='dx-datagrid-content')
    target_table = None
    if datagrid_content_div:
        candidate_table = datagrid_content_div.find('table', class_='dx-datagrid-table')
        if candidate_table and candidate_table.find('tr', class_='dx-data-row'):
            target_table = candidate_table

    if not target_table:
        all_tables = soup.find_all('table', class_='dx-datagrid-table')
        for table_candidate in all_tables:
            if table_candidate.find('tr', class_='dx-data-row'):
                target_table = table_candidate
                break

    if not target_table:
        print("Could not find the specific data table containing 'dx-data-row' rows.")
        return None

    rows = target_table.find_all('tr', class_='dx-data-row')

    if not rows:
        print("No data rows (tr with class 'dx-data-row') found in the identified table.")
        return None

    print(f"Found {len(rows)} potential data rows to process.")

    for i, row in enumerate(rows):
        cells = row.find_all('td')

        if len(cells) >= 2:
            hour_cell = cells[0]
            hour_range_str = hour_cell.get_text(strip=True)
            price_cell = cells[1]
            price_str = price_cell.get_text(strip=True)
            price_str_cleaned = price_str.replace('.', '').replace(',', '.')

            try:
                price_float = float(price_str_cleaned)
                hourly_prices_data.append({
                    "Hour": hour_range_str,
                    "Price (€/MWh)": price_float
                })
            except ValueError:
                print(
                    f"Warning: Row {i + 1}: Could not convert price '{price_str}' (cleaned: '{price_str_cleaned}') to float for hour '{hour_range_str}'.")
        else:
            print(
                f"Warning: Row {i + 1} has {len(cells)} cells, expected at least 2. Text: {[c.get_text(strip=True) for c in cells]}")

    if not hourly_prices_data:
        print("No price data could be extracted from the rows.")
        return None

    df = pd.DataFrame(hourly_prices_data)
    if len(df) != 24:
        print(f"Warning: Expected 24 hourly prices, but found {len(df)}.")

    return df


if __name__ == '__main__':
    target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    # can use fixed date for testing
    # target_date = "2025-05-20"

    nord_pool_url = f"https://data.nordpoolgroup.com/auction/day-ahead/prices?deliveryDate={target_date}&currency=EUR&aggregation=DeliveryPeriod&deliveryAreas=EE"

    print(f"Targeting Nord Pool URL: {nord_pool_url}")

    rendered_html = get_html_with_selenium(nord_pool_url, wait_for_class="dx-data-row")

    if rendered_html:
        df_prices = parse_rendered_nordpool_html(rendered_html)

        if df_prices is not None and not df_prices.empty:
            df_prices['Date'] = target_date
            print("\n--- Successfully Extracted Data ---")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(df_prices)

            try:
                average_price = df_prices['Price (€/MWh)'].mean()
                print(f"\nAverage Daily Price on {target_date}: {average_price:.2f} €/MWh")
            except KeyError:
                print("\nCould not calculate average price, 'Price (€/MWh)' column not found.")
            except Exception as e:
                print(f"\nError calculating average price: {e}")
        else:
            print("\nFailed to parse price data from the HTML.")
        if df_prices is not None and not df_prices.empty:
            print("\n--- Creating Visualization ---")
            try:
                if 'Start Hour' not in df_prices.columns:
                    plot_hours = df_prices['Hour']
                else:
                    plot_hours = df_prices['Start Hour']

                plt.figure(figsize=(12, 6))
                plt.plot(plot_hours, df_prices['Price (€/MWh)'], marker='o', linestyle='-')

                plt.title(f'Hourly Electricity Prices for Estonia on {target_date}')
                plt.xlabel('Hour of the Day')
                plt.ylabel('Price (€/MWh)')
                plt.grid(True)

                if 'Start Hour' in df_prices.columns:
                    plt.xticks(df_prices['Start Hour'])
                else:
                    plt.xticks(rotation=45, ha="right")  # rotate if using "00 - 01" labels

                plt.tight_layout()

                # save the plot to a file to /visualizations
                visualizations_dir = "visualizations"
                os.makedirs(visualizations_dir, exist_ok=True)

                plot_filename = os.path.join(visualizations_dir, f"nordpool_prices_{target_date}.png")
                plt.savefig(plot_filename)
                print(f"Visualization saved as {plot_filename}")

                plt.show()

            except Exception as e:
                print(f"Error creating visualization: {e}")
    else:
        print("\nFailed to retrieve rendered HTML using Selenium.")

    print("\n--- Script Finished ---")
