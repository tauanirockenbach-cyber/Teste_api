import streamlit as st

from app.services.weather_api import get_weather


st.set_page_config(
    page_title="Consulta Meteorológica",
    page_icon="🌤️",
    layout="centered",
)


st.title("🌤️ Consulta Meteorológica")

st.write(
    "Consulte as condições climáticas atuais "
    "de uma localidade utilizando uma API."
)


city = st.text_input(
    "Digite uma cidade:",
    placeholder="Ex.: Rio de Janeiro",
)


if st.button("Consultar clima"):

    if not city.strip():
        st.warning("Informe uma cidade.")

    else:
        try:
            data = get_weather(city)

            current = data["current"]
            location = data["location"]

            temperature = current["temp_c"]
            humidity = current["humidity"]
            feels_like = current["feelslike_c"]
            condition = current["condition"]["text"]

            st.success(
                f"Clima encontrado para "
                f"{location['name']}."
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Temperatura",
                    f"{temperature} °C",
                )

            with col2:
                st.metric(
                    "Sensação térmica",
                    f"{feels_like} °C",
                )

            col3, col4 = st.columns(2)

            with col3:
                st.metric(
                    "Umidade",
                    f"{humidity}%",
                )

            with col4:
                st.write("**Condição**")
                st.write(condition)

        except Exception as error:
            st.error(
                f"Não foi possível consultar o clima: {error}"
            )