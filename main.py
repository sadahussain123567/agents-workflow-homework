import streamlit as st
import os
import requests
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, function_tool
from agents.run import RunConfig

# Load environment variables
load_dotenv()

@function_tool
def get_weather(city) -> str:
    key = os.getenv("Weather_api")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get("cod") != 200:
        return f"Sorry, weather for {city} not found."

    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    return f"Today in {city}, the weather is '{description}' with a temperature of {temp}°C."

# Gemini Agent setup
api_key = os.getenv("Gemini_key")
external_file = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_file
)
config = RunConfig(model=model, model_provider=external_file, tracing_disabled=True)


st.set_page_config(page_title="🎇 Weather Checker App")
st.title("🌤️Weather checker Agent")
st.markdown("Get real-time weather updates. Select a city and press the button!")

# City selection
cities = ["Karachi", "Lahore", "Islamabad", "Hyderabad", "Peshawar", "Multan"]
selected_city = st.selectbox("Choose a city:", ["-- Select City --"] + cities)

# Button to check weather
if selected_city != "-- Select City --" and st.button("✅ Check Weather"):
    
    async def run_agent(city):
        agent = Agent(
            name="WeatherAgent",
            instructions="Always use the tool to get weather. Never guess.",
            tools=[get_weather]
        )
        return await Runner.run(agent, f"What is the weather in {city}?", run_config=config)

    with st.spinner(f"Checking weather in {selected_city}..."):
        try:
            result = asyncio.run(run_agent(selected_city))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_agent(selected_city))

        st.success(result.final_output)
