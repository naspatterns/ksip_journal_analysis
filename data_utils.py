import pandas as pd

def load_and_clean_data(filepath='인도철학_통합.csv'):
    """
    데이터 클렌징 로직
    - 다중 저자 케이스 분리 (',' 또는 ';')
    - 신규 저자 추적 (1989년을 기점, set() 활용)
    """
    df = pd.read_csv(filepath)
    
    # 결측치 처리
    df['발행연도'] = pd.to_numeric(df['발행연도'], errors='coerce')
    df = df.dropna(subset=['발행연도']).copy()
    df['발행연도'] = df['발행연도'].astype(int)
    
    # 저자명, 키워드 결측치 처리
    df['저자명'] = df['저자명'].fillna('')
    df['저자키워드'] = df['저자키워드'].fillna('')
    
    # 저자 및 키워드 파싱 로직용 추가 DataFrame들 생성
    author_stats_df = process_authors(df)
    keyword_df = process_keywords(df)
    
    return df, author_stats_df, keyword_df

def process_authors(df):
    """
    연도별 저자 수를 계산하고,
    신규 저자(기존에 등장하지 않았던 저자)를 판별하여 데이터프레임으로 반환합니다.
    """
    author_records = []
    for _, row in df.iterrows():
        year = row['발행연도']
        authors_str = str(row['저자명']).strip()
        if not authors_str or authors_str == 'nan':
            continue
            
        # 다중 저자 분리 (콤마, 세미콜론 기준)
        authors = [a.strip() for a in authors_str.replace(';', ',').split(',') if a.strip()]
        for author in authors:
            author_records.append({'발행연도': year, '저자': author})
            
    authors_df = pd.DataFrame(author_records)
    if authors_df.empty:
        return pd.DataFrame()
        
    authors_df = authors_df.sort_values('발행연도')
    
    # 연도별 누적 저자 set() 관리 (1989년 저자는 모두 신규)
    yearly_stats = []
    seen_authors = set()
    
    for year, group in authors_df.groupby('발행연도'):
        current_authors = set(group['저자'].unique())
        
        # 신규 저자는 올해 등장한 저자 중 기존 seen_authors에 없는 저자
        new_authors = current_authors - seen_authors
        
        total_count = len(current_authors)
        new_count = len(new_authors)
        new_ratio = (new_count / total_count * 100) if total_count > 0 else 0
        
        yearly_stats.append({
            '발행연도': year,
            '총 참여 저자 수': total_count,
            '신규 저자 수': new_count,
            '신규 저자 비율(%)': new_ratio
        })
        
        # 누적 저자 세트 업데이트
        seen_authors.update(current_authors)
        
    return pd.DataFrame(yearly_stats)

def process_keywords(df):
    """
    국문/영문/산스크리트어(IAST)가 혼재된 키워드를 분리 및 정제합니다.
    """
    keyword_records = []
    
    # 문서 단위로 키워드 스플릿
    for _, row in df.iterrows():
        year = row['발행연도']
        keywords_str = str(row['저자키워드']).strip()
        if not keywords_str or keywords_str == 'nan':
            continue
            
        # 쉼표 기준으로 스플릿
        keywords = [k.strip().lower() for k in keywords_str.split(',') if k.strip()]
        for kw in keywords:
            keyword_records.append({
                '발행연도': year,
                '키워드': kw
            })
            
    return pd.DataFrame(keyword_records)

def get_keyword_trends(keyword_df, top_n=5, window=3):
    """이동평균분석용 시계열 데이터 프레임 변환"""
    if keyword_df.empty:
        return pd.DataFrame()
    
    # 전체 기간 상위 키워드 추출
    top_keywords = keyword_df['키워드'].value_counts().head(top_n).index.tolist()
    
    # 연도별 키워드 빈도 계산
    yearly_kw = keyword_df.groupby(['발행연도', '키워드']).size().reset_index(name='빈도')
    top_yearly = yearly_kw[yearly_kw['키워드'].isin(top_keywords)]
    
    # 피벗 후 이동평균 적용
    pivot_df = top_yearly.pivot(index='발행연도', columns='키워드', values='빈도').fillna(0)
    ma_df = pivot_df.rolling(window=window, min_periods=1).mean().reset_index()
    
    return ma_df.melt(id_vars=['발행연도'], value_name='이동평균_빈도')
