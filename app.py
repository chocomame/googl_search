import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import pandas as pd
import concurrent.futures

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def search_goo_gl_urls(url):
    if not is_valid_url(url):
        return url, [], "無効なURL"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return url, [], f"エラー: {str(e)}"
    soup = BeautifulSoup(response.text, 'html.parser')
    
    goo_gl_pattern = re.compile(r'https://goo\.gl/\S+')
    goo_gl_urls = goo_gl_pattern.findall(str(soup))
    
    return url, list(set(goo_gl_urls)), None

def process_urls(urls):
    results = {}
    for url in urls:
        url = url.strip()
        try:
            main_url, goo_gl_urls, error = search_goo_gl_urls(url)
            domain = urlparse(main_url).netloc
            if domain not in results:
                results[domain] = {"URL": main_url, "goo.gl URLs": [], "エラー": error or ''}
            results[domain]["goo.gl URLs"].extend(goo_gl_urls)

            additional_urls = [urljoin(url, path) for path in ['/access/', '/access.html']]
            for additional_url in additional_urls:
                try:
                    _, additional_goo_gl_urls, _ = search_goo_gl_urls(additional_url)
                    if additional_goo_gl_urls:
                        results[domain]["goo.gl URLs"].extend(additional_goo_gl_urls)
                        results[domain][additional_url] = ', '.join(additional_goo_gl_urls)
                    else:
                        results[domain][additional_url] = ''
                except requests.RequestException as e:
                    print(f"{additional_url} にアクセスできませんでした: {str(e)}")
        except Exception as e:
            domain = urlparse(url).netloc
            results[domain] = {"URL": url, "goo.gl URLs": [], "エラー": f"予期せぬエラー: {str(e)}"}

    return results

st.title('複数サイト対応 goo.gl 検索ツール')
st.markdown('ver1.02：ユーザーが入力した並び順通りに出力されるように修正')
st.markdown('ver1.03：TOPのみではなくアクセスページも検索するよう修正')
urls = st.text_area('調査するウェブサイトのURLを1行に1つずつ入力してください:')

if st.button('検索'):
    if urls:
        urls_list = [url.strip() for url in urls.split('\n') if url.strip()]
        with st.spinner('検索中...'):
            results = process_urls(urls_list)
        
        # 結果の表示
        if results:
            df = pd.DataFrame(results).T.reset_index()
            df = df.rename(columns={'index': 'ドメイン', 0: 'URL'})
            df['メインページ goo.gl URLs'] = df['ドメイン'].apply(lambda x: ', '.join(results[x]['goo.gl URLs']))
            df['アクセスページ'] = ''
            df['アクセスページ goo.gl URLs'] = ''
            for i, row in df.iterrows():
                domain = row['ドメイン']
                access_pages = [k for k, v in results[domain].items() if k != 'URL' and k != 'goo.gl URLs' and k != 'エラー']
                df.at[i, 'アクセスページ'] = ', '.join(access_pages)
                access_goo_gl_urls = [v for k, v in results[domain].items() if k != 'URL' and k != 'goo.gl URLs' and k != 'エラー' and v]
                df.at[i, 'アクセスページ goo.gl URLs'] = ', '.join(access_goo_gl_urls)
            df['エラー'] = df['ドメイン'].apply(lambda x: results[x]['エラー'])
            st.dataframe(df[['ドメイン', 'URL', 'メインページ goo.gl URLs', 'アクセスページ', 'アクセスページ goo.gl URLs', 'エラー']])
        else:
            st.warning("goo.glリンクは見つかりませんでした。")
        
        csv = pd.DataFrame(results).T.to_csv().encode('utf-8')
        st.download_button(
            label="結果をCSVでダウンロード",
            data=csv,
            file_name="goo_gl_search_results.csv",
            mime="text/csv",
        )
    else:
        st.warning('URLを少なくとも1つ入力してください。')