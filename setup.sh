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
primaryColor = '#1DB954'\n\
backgroundColor = '#191414'\n\
secondaryBackgroundColor = '#1DB954'\n\
textColor = '#FFFFFF'\n\
font = 'sans serif'\n\
" >> ~/.streamlit/config.toml