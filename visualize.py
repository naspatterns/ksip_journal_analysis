import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import platform

# 한글 폰트 설정 (Mac)
if platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
    
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

def plot_yearly_papers(df):
    """
    연도별 논문 게재 수 플롯 (Plotly 활용)
    """
    yearly_counts = df.groupby('발행연도').size().reset_index(name='논문 게재 수')
    
    fig = px.line(
        yearly_counts, 
        x='발행연도', 
        y='논문 게재 수', 
        title='연도별 논문 게재 수 트렌드',
        markers=True,
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title="발행연도",
        yaxis_title="논문 수",
        hovermode="x unified"
    )
    return fig

# TODO: 추가 시각화 함수 구성
def plot_yearly_authors(author_stats_df):
    if author_stats_df.empty:
        return None
    fig = px.line(
        author_stats_df, 
        x='발행연도', 
        y='총 참여 저자 수', 
        title='연도별 총 참여 저자 수 트렌드',
        markers=True,
        template='plotly_white'
    )
    fig.update_layout(xaxis_title="발행연도", yaxis_title="저자 수", hovermode="x unified")
    return fig

def plot_new_author_metrics(author_stats_df):
    if author_stats_df.empty:
        return None
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=author_stats_df['발행연도'], y=author_stats_df['신규 저자 수'], name="신규 저자 수", opacity=0.7),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=author_stats_df['발행연도'], y=author_stats_df['신규 저자 비율(%)'], name="신규 비율(%)", mode='lines+markers'),
        secondary_y=True,
    )
    fig.update_layout(title_text="신규 저자 유입 지표", template='plotly_white', hovermode="x unified")
    fig.update_yaxes(title_text="신규 저자 수", secondary_y=False)
    fig.update_yaxes(title_text="신규 저자 비율 (%)", range=[0, 105], secondary_y=True)
    return fig

def plot_keyword_wordcloud(keyword_df):
    if keyword_df.empty:
        return None
    from wordcloud import WordCloud
    
    text = " ".join(keyword_df['키워드'].tolist())
    font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc' if platform.system() == 'Darwin' else None
    
    wordcloud = WordCloud(
        font_path=font_path,
        width=800, 
        height=400, 
        background_color='white',
        collocations=False
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    return fig

def plot_keyword_trends(ma_df):
    if ma_df.empty:
        return None
    fig = px.line(
        ma_df,
        x='발행연도',
        y='이동평균_빈도',
        color='키워드',
        title='주요 키워드 시계열 트렌드 (3년 이동평균)',
        template='plotly_white',
    )
    fig.update_layout(hovermode="x unified")
    return fig

def plot_keyword_treemap(keyword_df):
    """학파/개념별 비중 트리맵 시각화"""
    if keyword_df.empty:
        return None
        
    top_kw = keyword_df['키워드'].value_counts().head(30).reset_index()
    top_kw.columns = ['키워드', '빈도']
    top_kw['범주'] = '주요 키워드'
    
    fig = px.treemap(
        top_kw,
        path=['범주', '키워드'],
        values='빈도',
        title='상위 30개 주요 키워드 비중 분포',
        color='빈도',
        color_continuous_scale='Blues'
    )
    return fig
