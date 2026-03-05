
import streamlit as st
import pickle

try:
    with open('brand_outputs.pkl', 'rb') as f:
        brand_outputs = pickle.load(f)

    st.title("Content Pillar Analysis Dashboard")

    if not brand_outputs:
        st.warning("No analysis data found.")
    else:
        brand = st.selectbox("Select Brand", list(brand_outputs.keys()))
        data = brand_outputs[brand]

        if isinstance(data, str):
            st.error(data)
        else:
            theme_names = [theme['theme'] for theme in data]
            #selected_theme = st.selectbox("Select Theme", theme_names)

            for theme in data:
                for share in theme['shares']:
                    for post in theme['posts']:
                        #if theme['theme'] == selected_theme:
                        st.header(theme['theme'])
                        st.subheader(share)
                        st.subheader(post)
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("Subtopics")
                            for subtopic in theme['subtopics']:
                                st.markdown(f"**{subtopic['subtopic']}**: {subtopic['description']}")

                        with col2:
                            st.subheader("Examples")
                            for example in theme['examples']:
                                st.markdown(f"- {example}")
except Exception as e:
    st.error("🚨 Streamlit app failed to load.")
    st.exception(e)
