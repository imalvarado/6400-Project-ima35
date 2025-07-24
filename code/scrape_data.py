import requests
import pandas as pd
import warnings
import re
from bs4 import BeautifulSoup
warnings.filterwarnings("ignore")


### FUNCTION DEFINITIONS

def retrieve_results_table(year):
    url = f"https://www.worldsurfleague.com/athletes/tour/mct?year={year}"
    response = requests.get(url)
    html_content = response.text
    raw_results = pd.read_html(html_content, header=1)[0]
    raw_results = raw_results.drop(["Rank", "Unnamed: 1", "Unnamed: 2", "Total Points"], axis=1)
    if "WSL Finals" in raw_results.columns:
        rows_to_drop = ["Final 5 Cutoff", "CT Requalification Line", "Mid-Season Cut Line"]
        raw_results = raw_results[~raw_results["Name"].isin(rows_to_drop)]
        raw_results = raw_results.drop(["WSL Finals"], axis=1)

    return raw_results


def clean_name_col(df):
    # clean name column
    countries = ["United States", "South Africa", "Australia", "France", 
                    "Brazil", "Hawaii", "Portugal", "New Zealand", "Japan",
                    "Ireland", "Spain", "Fiji", "Italy", "French Polynesia",
                    "Indonesia"]
    clean_names = []
    for value in df["Name"]:
        # remove country and tag from name
        name_country = ""
        tags = [" (REP)", " (RET)", " (INJ)", " (WDN)"]
        rem_tag = ""
        for country in countries:
            if country in value:
                name_country = country
        for tag in tags:
            if tag in value:
                rem_tag = tag
        clean_names.append(value.replace(name_country, "").replace(rem_tag, "").strip())
    df["Name"] = clean_names

    return df


def clean_placement_data(df):

    # loop over columns in results
    for col in df.columns:

        if col == "Name":
            continue

        # get placement mapping (sorted list of placement scores)
        col_values = list(df[col].unique())
        col_values = [str(i).replace("*", "").replace(",", "").strip() for i in col_values]
        try:
            col_values.remove("-")
        except:
            pass
        try:
            col_values.remove('-') # this is somehow different from the one above
        except:
            pass
        col_values = [int(i) for i in col_values]
        col_values.sort(reverse=True)
        
        # build clean column
        clean_values = []
        for value in df[col]:
            clean_val = str(value).replace("*", "").replace(",", "").strip()
            if clean_val == "-":
                clean_values.append(pd.NA)
            else:
                clean_values.append(col_values.index(int(clean_val))+1)

        # replace with clean column
        df[col] = clean_values

    return df


def add_event_names(df, year):
    url = f"https://www.worldsurfleague.com/athletes/tour/mct?year={year}"
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    table_header = soup.find("thead")
    table_header = table_header.find("tr", class_="last")
    cells = table_header.find_all("th", class_="athlete-event-place")

    new_colnames = ["Name"]
    for cell in cells:
        tooltip_info = cell.find("span", class_="tooltip-item")["data-tooltip"]
        event_name = tooltip_info.split("/")[-3].split("\\")[0]
        if "-presented-by-" in event_name:
            event_name = event_name.split("-presented-by-")[0]
        new_colnames.append(event_name)

    df.columns = new_colnames

    return df


def clean_event_names(df):
    new_columns = []

    for colname in list(df.columns):
        event_name = colname.lower()

        if "portugal" in event_name:
            new_columns.append("portugal")

        elif "j-bay" in event_name:
            new_columns.append("j-bay")

        elif "fiji" in event_name:
            new_columns.append("fiji")

        elif "trestles" in event_name:
            new_columns.append("trestles")

        elif "rio" in event_name:
            new_columns.append("rio")

        elif "bali" in event_name:
            new_columns.append("bali")

        elif "margaret" in event_name:
            new_columns.append("margaret-river")
        
        elif "teahupoo" in event_name or "tahiti" in event_name:
            new_columns.append("teahupoo")

        else:
            new_columns.append(colname)

    df.columns = new_columns
    return df

###


### SCRAPE WSL CT RESULTS PAGES


# set year range
first_year = 2010; last_year = 2022
years = [str(y) for y in range(first_year, last_year+1)]
if "2020" in years:
    years.remove("2020")

# loop over years
for year in years:

    print(f"Getting data for {year}...")

    # get raw results
    raw_results = retrieve_results_table(year)

    # clean names column
    results = clean_name_col(raw_results)

    # clean placement data
    results = clean_placement_data(results)

    # change column names to events
    results = add_event_names(results, year)

    # clean event names
    results = clean_event_names(results)

    # save results to csv
    results.to_csv(f"../data/wsl_results_{year}.csv", index=False)

    print(f"Successfully got data for {year}.")