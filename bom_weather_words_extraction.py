#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script extracts content from each tab on the Bureau of Meteorology's
Weather Words page: http://www.bom.gov.au/info/wwords/

It specifically looks for term-definition pairs where a term is presented
in a <p><strong>Term</strong></p> format, followed by its definition in
the next <p>Definition</p> tag.

The script targets the tab structure using 'tabberlive' and 'tabbertab' classes.

Dependencies:
  - requests (for fetching the webpage)
  - beautifulsoup4 (for parsing HTML)

You can install them using pip:
  pip install requests beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup, Tag


def extract_weather_words_from_bom(url: str) -> dict | None:
    """
    Fetches and parses the BOM Weather Words page to extract terms and definitions
    from each tab.

    Args:
        url: The URL of the BOM Weather Words page.

    Returns:
        A dictionary where keys are tab titles and values are lists of
        dictionaries, each containing a 'term' and 'definition'.
        Returns None if the page cannot be fetched or parsed.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL '{url}': {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    all_tabs_data = {}

    # Find the main container for all tabs
    # Find the main container for all tabs (class="tabber")
    tabber_main_container = soup.find("div", class_="tabber")

    if not tabber_main_container:
        print(
            "Main tab container 'div.tabber' not found. The page structure might have changed."
        )
        return None

    # Find all individual tab content divs.
    # These divs have class 'tabbertab' and also a 'title' attribute which is the tab name.
    # This will also match divs with class "tabbertab tabbertabhide".
    tab_content_divs = tabber_main_container.find_all(
        "div", class_="tabbertab", recursive=False
    )

    if not tab_content_divs:
        print(
            "No 'div.tabbertab' elements found within 'div.tabber'. No tab content to parse."
        )
        return None

    for content_div in tab_content_divs:
        tab_title = content_div.get("title")
        # if not tab_title:
        #    print(
        #        "Warning: A 'div.tabbertab' was found without a 'title' attribute. Skipping this tab."
        #    )
        #    continue

        current_tab_items = []
        processed_terms_in_tab = (
            set()
        )  # To avoid duplicates if a term appears in multiple structures

        # Strategy 1: Extract from <dl> <dt>/<dd> structure
        definition_lists = content_div.find_all(
            "dl", recursive=False
        )  # Direct <dl> children
        for dl_element in definition_lists:
            current_dt_tag = None
            for child_node in dl_element.children:
                if not isinstance(
                    child_node, Tag
                ):  # Skip NavigableString like newlines
                    continue

                if child_node.name == "dt":
                    current_dt_tag = child_node
                elif child_node.name == "dd" and current_dt_tag:
                    term_text = (
                        current_dt_tag.get_text(strip=True).replace(":", "").strip()
                    )

                    # Consolidate definition text from <dd>
                    # Use get_text with a separator and then normalize whitespace
                    definition_text_final = " ".join(
                        child_node.get_text(separator=" ", strip=True).split()
                    )

                    if term_text and term_text not in processed_terms_in_tab:
                        current_tab_items.append(
                            {
                                "term": term_text,
                                "definition": definition_text_final or None,
                            }
                        )
                        processed_terms_in_tab.add(term_text)
                    current_dt_tag = None  # Reset for the next <dt>

        # Strategy 2: Extract from <p><strong>Term</strong></p> <p>Definition</p> structure
        # This is for content not in <dl> or for tabs structured this way.
        paragraphs = content_div.find_all("p", recursive=False)
        i = 0
        while i < len(paragraphs):
            p_current = paragraphs[i]

            strong_tags_in_p = p_current.find_all("strong")
            is_term_paragraph = False
            term_text_p = None

            if len(strong_tags_in_p) == 1:
                # Check if the stripped text of the <p> tag is identical to the
                # stripped text of its <strong> child.
                if p_current.get_text(strip=True) == strong_tags_in_p[0].get_text(
                    strip=True
                ):
                    is_term_paragraph = True
                    term_text_p = (
                        strong_tags_in_p[0]
                        .get_text(strip=True)
                        .replace(":", "")
                        .strip()
                    )

            if (
                is_term_paragraph
                and term_text_p
                and term_text_p not in processed_terms_in_tab
            ):
                definition_text_p = None
                # Check if the next paragraph exists and is a definition
                if i + 1 < len(paragraphs):
                    p_next = paragraphs[i + 1]

                    # The next paragraph is a definition if it's NOT a term paragraph itself.
                    strong_tags_in_p_next = p_next.find_all("strong")
                    p_next_is_term = False
                    if len(strong_tags_in_p_next) == 1:
                        if p_next.get_text(strip=True) == strong_tags_in_p_next[
                            0
                        ].get_text(strip=True):
                            p_next_is_term = True

                    if not p_next_is_term:
                        definition_text_p = p_next.get_text(strip=True)
                        current_tab_items.append(
                            {"term": term_text_p, "definition": definition_text_p}
                        )
                        processed_terms_in_tab.add(term_text_p)
                        i += 1  # Increment to skip this definition paragraph
                    else:
                        # Next paragraph is another term, so current term has no definition
                        current_tab_items.append(
                            {"term": term_text_p, "definition": None}
                        )
                        processed_terms_in_tab.add(term_text_p)
                else:
                    # Term is the last paragraph, or no suitable definition paragraph follows
                    current_tab_items.append({"term": term_text_p, "definition": None})
                    processed_terms_in_tab.add(term_text_p)

            i += 1

        all_tabs_data[tab_title] = current_tab_items

    return all_tabs_data


def main():
    """
    Main function to run the extraction and print the results.
    """
    target_url = "http://www.bom.gov.au/info/wwords/"
    print(f"Attempting to extract weather words from: {target_url}\n")

    weather_data = extract_weather_words_from_bom(target_url)

    if weather_data:
        for tab_title, items_list in weather_data.items():
            print(f"--- {tab_title} ---")
            if items_list:
                for item in items_list:
                    term = item["term"]
                    definition = item["definition"]
                    print(f"  Term: {term}")
                    if definition:
                        print(f"  Definition: {definition}")
                    else:
                        print(f"  Definition: (Not provided or not in expected format)")
                    print()
            else:
                print(
                    "  (No term-definition pairs found in the expected format for this tab.)\n"
                )
    else:
        print("Could not retrieve or parse data from the website.")


if __name__ == "__main__":
    main()
