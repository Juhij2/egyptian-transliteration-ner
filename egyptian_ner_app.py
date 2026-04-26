import streamlit as st
import spacy
import pandas as pd
from collections import Counter
import zipfile
import os

st.set_page_config(page_title="Egyptian Transliteration NER", page_icon="𓂀", layout="wide")

@st.cache_resource
def load_model():
    if not os.path.exists('egyptian_ner_model'):
        with zipfile.ZipFile('egyptian_ner_model.zip', 'r') as z:
            z.extractall('egyptian_ner_model')
    return spacy.load('egyptian_ner_model')

nlp = load_model()

DEITY_INFO = {
    'wsꞽr': 'Osiris — god of the dead and resurrection',
    'ḥr.w': 'Horus — falcon-headed sky god',
    'rꜥw': 'Ra — sun god',
    'ꞽnp.w': 'Anubis — god of embalming',
    'stš': 'Seth — god of chaos',
    'gbb': 'Geb — earth god',
    'nw.t': 'Nut — sky goddess',
    'ꞽs.t': 'Isis — goddess of magic',
    'ptḥ': 'Ptah — creator god of Memphis',
    'sḫm.t': 'Sekhmet — lion-headed goddess of war',
    'ꞽmn': 'Amun — king of the gods',
    'ḏḥwtꞽ': 'Thoth — god of wisdom and writing',
    'ḥwt-ḥr': 'Hathor — goddess of love and beauty',
    'n(ꞽ).t': 'Neith — goddess of war and weaving',
}

st.title("𓂀 Egyptian Transliteration NER")
st.markdown("Named Entity Recognition for ancient Egyptian transliteration — identifies **deities** and **persons** directly from Leiden Unified Transliteration text.")
st.markdown("---")

mode = st.radio("Mode", ["Single Text", "Batch Analysis"], horizontal=True)
st.markdown("---")

if mode == "Single Text":
    st.markdown("### Enter Egyptian transliteration text")

    examples = [
        "wsꞽr nb ꜣbḏw ḥr.w nṯr ꜥꜣ",
        "dd.ꞽn rꜥw n wsꞽr stš ḫft.ꞽ n ḥr.w",
        "ꞽnp.w tp-ḏw=f sꜣ wsꞽr nṯr ꜥꜣ",
        "ꞽmn-rꜥw nb nswt tꜣ.wj ptḥ nb mꜣꜥ.t",
    ]

    selected = st.selectbox("Or pick an example:", ["— type your own —"] + examples)

    if selected == "— type your own —":
        text = st.text_area("Transliteration text:", height=100, placeholder="e.g. wsꞽr nb ꜣbḏw")
    else:
        text = st.text_area("Transliteration text:", value=selected, height=100)

    if text.strip():
        doc = nlp(text)

        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.markdown("#### Identified Entities")
            if doc.ents:
                highlighted = text
                offset = 0
                for ent in doc.ents:
                    color = "#d4a54a" if ent.label_ == "DEITY" else "#7a9cc0"
                    tag = f'<mark style="background:{color};padding:2px 6px;border-radius:4px;font-weight:600">{ent.text} <sup style="font-size:10px">{ent.label_}</sup></mark>'
                    highlighted = highlighted[:ent.start_char + offset] + tag + highlighted[ent.end_char + offset:]
                    offset += len(tag) - len(ent.text)
                st.markdown(highlighted, unsafe_allow_html=True)
            else:
                st.info("No entities found.")

        with col2:
            st.markdown("#### Entity Details")
            for ent in doc.ents:
                icon = "✦" if ent.label_ == "DEITY" else "◆"
                st.markdown(f"**{icon} {ent.text}** `{ent.label_}`")
                if ent.text in DEITY_INFO:
                    st.caption(DEITY_INFO[ent.text])

else:
    st.markdown("### Batch Analysis — paste multiple sentences")
    batch_text = st.text_area("One sentence per line:", height=200,
        placeholder="wsꞽr nb ꜣbḏw\ndd.ꞽn rꜥw n wsꞽr\nꞽnp.w tp-ḏw=f ḥr.w nṯr ꜥꜣ")

    if batch_text.strip():
        sentences = [s.strip() for s in batch_text.strip().split('\n') if s.strip()]

        all_entities = []
        for sent in sentences:
            doc = nlp(sent)
            for ent in doc.ents:
                all_entities.append({
                    'entity': ent.text,
                    'type': ent.label_,
                    'sentence': sent
                })

        if all_entities:
            ent_df = pd.DataFrame(all_entities)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Deity Mentions")
                deities = ent_df[ent_df['type'] == 'DEITY']
                if not deities.empty:
                    for entity, count in Counter(deities['entity']).most_common():
                        info = DEITY_INFO.get(entity, "")
                        st.markdown(f"**{entity}** — {count}x {f'· *{info}*' if info else ''}")
                else:
                    st.info("No deities found.")

            with col2:
                st.markdown("#### Person Mentions")
                persons = ent_df[ent_df['type'] == 'PERSON']
                if not persons.empty:
                    for entity, count in Counter(persons['entity']).most_common():
                        st.markdown(f"**{entity}** — {count}x")
                else:
                    st.info("No persons found.")

            st.markdown("---")
            st.markdown(f"**Summary:** {len(sentences)} sentences, {len(all_entities)} entities found ({len(deities)} deities, {len(persons)} persons)")
        else:
            st.info("No entities found in the provided text.")

st.markdown("---")
st.markdown("**Model:** spaCy NER trained on 7,059 TLA sentences | **F1:** 95.6% | **Classes:** DEITY, PERSON | **Script:** Leiden Unified Transliteration")
