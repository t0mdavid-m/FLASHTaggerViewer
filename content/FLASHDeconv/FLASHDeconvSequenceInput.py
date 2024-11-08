import streamlit as st
import re
from src.common.common import page_setup, save_params, v_space

fixed_mod_cysteine = ['No modification',
                      'Carbamidomethyl (+57)',
                      'Carboxymethyl (+58)',
                      'Xlink:Disulfide (-1 per C)']
                      # 'S-carboxamidoethyl-L-cysteine',
                      # 'S-carboxamidoethly-L-cysteine',
                      # 'S-pyridylethyl-L-cysteine',
                      # 'S-carboxamidomethly-L-cysteine',
                      # 'cyteine mercaptoethanol']
fixed_mod_methionine = ['No modification',
                        'L-methionine sulfoxide (+16)',
                        'L-methionine sulfone (+32)']


def validateSequenceInput(input_seq):
    # remove all white spaces
    seq = ''.join(input_seq.split())
    if not seq: return False

    pattern = re.compile("^[ac-ik-wyAC-IK-WYXx]+$")  # only alphabet except for BJXZ
    if not pattern.match(seq):
        return False
    return True


def emptySequenceInput():
    for key in ['input_sequence', 'fixed_mod_cysteine', 'fixed_mod_methionine']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['reset_sequence_input'] = True


# page initialization
params = page_setup()

# for resetting the form (cannot be done after form is instantiated)
if 'reset_sequence_input' not in st.session_state:
    st.session_state['reset_sequence_input'] = False

# title and reset buttons
c1, c2 = st.columns([8, 1])
c1.title("Proteoform Sequence Input")
v_space(1, c2)
if c2.button('Reset'):
    emptySequenceInput()

# if any sequence was submitted before
if 'input_sequence' in st.session_state and st.session_state.input_sequence \
        and 'sequence_text' not in st.session_state:
    st.session_state['sequence_text'] = st.session_state.input_sequence
# if any modification was submitted before
if 'fixed_mod_cysteine' in st.session_state and st.session_state.fixed_mod_cysteine \
        and 'selected_fixed_mod_cysteine' not in st.session_state:
    st.session_state['selected_fixed_mod_cysteine'] = st.session_state.fixed_mod_cysteine
if 'fixed_mod_methionine' in st.session_state and st.session_state.fixed_mod_methionine \
        and 'selected_fixed_mod_methionine' not in st.session_state:
    st.session_state['selected_fixed_mod_methionine'] = st.session_state.fixed_mod_methionine

# clean up the entries of form, if needed
if st.session_state['reset_sequence_input']:
    st.session_state['sequence_text'] = ''
    st.session_state['selected_fixed_mod_cysteine'] = 'No modification'
    st.session_state['selected_fixed_mod_methionine'] = 'No modification'
    st.session_state['reset_sequence_input'] = False

with st.form('sequence_input'):
    # sequence
    st.text_area('Proteoform sequence', key='sequence_text')

    # fixed modification
    c1, c2 = st.columns(2)
    c1.selectbox('Fixed modification: Cysteine', fixed_mod_cysteine,
                 key='selected_fixed_mod_cysteine', placeholder='No modification')
    c2.selectbox('Fixed modification: Methionine', fixed_mod_methionine,
                 key='selected_fixed_mod_methionine', placeholder='No modification')
    _, c2 = st.columns([8, 1])
    submitted = c2.form_submit_button("Save")
    if submitted:
        if 'input_sequence' in st.session_state:  # initialize
            del st.session_state['input_sequence']
        if st.session_state['sequence_text'] == '':
            emptySequenceInput()
            st.rerun()
        elif validateSequenceInput(st.session_state['sequence_text']):
            st.success('Proteoform sequence is submitted: ' + st.session_state['sequence_text'])
            # save information for sequence view
            st.session_state['input_sequence'] = ''.join(st.session_state['sequence_text'].split()).upper()

            st.session_state['fixed_mod_cysteine'], st.session_state['fixed_mod_methionine'] = '', ''
            if 'selected_fixed_mod_cysteine' in st.session_state \
                    and st.session_state['selected_fixed_mod_cysteine'] != 'No modification':
                st.session_state['fixed_mod_cysteine'] = st.session_state.selected_fixed_mod_cysteine
            if 'selected_fixed_mod_methionine' in st.session_state \
                    and st.session_state['selected_fixed_mod_methionine'] != 'No modification':
                st.session_state['fixed_mod_methionine'] = st.session_state.selected_fixed_mod_methionine
        else:
            st.error('Error: sequence input is not valid')

st.info("""
**💡 NOTE** 

- This is only needed when the "Sequence View" component will be used in 👀Viewer
        
- Variable modifications can be specified within the ”Sequence View” component in 👀Viewer.

- Only one protein sequence is allowed
""")

save_params(params)
