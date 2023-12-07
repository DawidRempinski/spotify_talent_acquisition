mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"dawid@rempinski.de\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml

echo "\
[theme]\n\
primaryColor = '#7792E3'\n\
backgroundColor = '#e6e6e6'\n\
secondaryBackgroundColor = '#eafbec'\n\
textColor = '#000000'\n\
font = 'sans serif'\n\
" >> ~/.streamlit/config.toml
