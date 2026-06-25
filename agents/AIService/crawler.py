"""

Sina Idea nadai kufanya hii kitu ajee, like how
"""

#TODO:
    # Make the driver headless
    # Structured Output e.g pydantic BaseModel

from smolagents import (
    tool,
    ToolCallingAgent,
    OpenAIModel,
    CodeAgent,
    GoogleSearchTool,
    VisitWebpageTool,
)
from smolagents.agents import ActionStep, MemoryStep
import markdownify
import requests
from helium import *
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
import os
from dotenv import load_dotenv
from time import sleep
from io import BytesIO
import PIL

load_dotenv()

driver: WebDriver = None
# ===============
# Tools
# ===============


@tool
def open_page(url: str) -> None:
    """It opens chrome and redirects to the url provided by the model

    Args:
        url (str): The url to be opened

    Returns:
        (WebDriver): A driver that can be used as arguements in other tools
    """
    global driver
    start_chrome(url)
    driver = get_driver()
    return


@tool
def click_something(text: str, driver: WebDriver = driver) -> None:
    """Used to click on clickables on a page

    Args:
        text (str): The text on the item to be clicked
        driver (WebDriver): The helium driver on the call obtained from open_page
    """

    click(text)


@tool
def key_in_a_field(text: str, key: str, driver: WebDriver = driver) -> None:
    """Used to input text to a field

    Args:
        text (str): The text to be keyed in
        key (str): The name on the field to be filled
        driver (WebDriver, optional): The helium driver. Defaults to driver.
    """
    write(text=text, into=key)


@tool
def calculate_height(driver: WebDriver = driver) -> int:
    """Calculates the height of the window viewport 

    Args:
        driver (WebDriver, optional): The helium driver. Defaults to driver.

    Returns:
        (int) : The window height of the current view of the page which can be used for scrolling
    """
    return driver.execute_script("return window.innerHeight")


@tool
def scroll(direction: int, pixels: int, driver: WebDriver = driver) -> None:
    """It Scrolls the page on a given direction on a given pixel size

    Args:
        direction (int): The direction of scroll 0 for up 1 for down; 2 for left; 3 for right;
        pixels (int): The size of the scroll
        driver (WebDriver, optional): The helium driver. Defaults to driver.
    """
    directions = {0: scroll_up, 1: scroll_down, 2: scroll_left, 3: scroll_right}
    directions[direction](num_pixels=pixels)


@tool
def close_popups() -> str:
    """
    Closes any visible modal or pop-up on the page. Use this to dismiss pop-up windows!
    This does not work on cookie consent banners.
    """
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()


def save_screenshot(memory_step: ActionStep, agent: ToolCallingAgent) -> None:
    sleep(1.0)
    current_step = memory_step.step_number
    global driver
    if driver is not None:
        for (
            previous_memory_step
        ) in (
            agent.memory.steps
        ):  # Remove previous screenshots from logs for lean processing
            if (
                isinstance(previous_memory_step, ActionStep)
                and previous_memory_step.step_number <= current_step - 2
            ):
                previous_memory_step.observations_images = None
        png_bytes = driver.get_screenshot_as_png()
        image = PIL.Image.open(BytesIO(png_bytes))
        print(f"Captured a browser screenshot: {image.size} pixels")
        memory_step.observations_images = [
            image.copy()
        ]  # Create a copy to ensure it persists, important!

        url_info = f"Current url: {driver.current_url}"
        memory_step.observations = (
            url_info
            if memory_step.observations is None
            else memory_step.observations + "\n" + url_info
        )
    return


agent = ToolCallingAgent(
    model=OpenAIModel(
        model_id="qwen3-vl:235b",
        api_base="https://ollama.com/v1",
        api_key=os.getenv("OLLAMA_API_KEY"),
    ),
    tools=[
        open_page,
        click_something,
        key_in_a_field,
        scroll,
        calculate_height,
        GoogleSearchTool(provider="serper"),
        VisitWebpageTool()
    ],
    step_callbacks=[save_screenshot],
)
