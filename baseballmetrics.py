import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as mc, matplotlib.patches as pat
from matplotlib.backends.backend_pdf import PdfPages 
import seaborn as sns
from PIL import Image
import copy, math, io, os, random, requests



def BA(df, mc = False): #Batting Average
    hit = ["Single", "Double", "Triple", "HomeRun"] # hitっていう変数作ります。
    df1 = df.reset_index(drop = True)
    ph = ['InPlay', 'HitByPitch'] # 変数
    kb = ['Strikeout', 'Walk'] # 変数
    df2 = df1.query('PitchCall == @ph or KorBB == @kb')
    ds = len(df2) #打席数
    sc = len(df2.query('PlayResult == "Sacrifice"')) + len(df2.query('TaggedHitType == "Bunt" and PlayResult == "FieldersChoice"')) + len(df2.query('TaggedHitType == "Bunt" and PlayResult == "Error"'))
    #犠牲打数
    ht = len(df2.query('PlayResult == @hit')) #安打数
    bb = len(df2.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    if ds-sc-bb != 0:
        ba = round(ht/(ds-sc-bb), 3) #打率
    else:
        ba = np.nan #分母が0の時の打率
    if mc:
        return ba, ds-sc-bb, ht
    else:
        return ba
    
def OBP(df, mc = True): #On-base Percentage
    hit = ["Single", "Double", "Triple", "HomeRun"] # hitっていう変数作ります。
    
    df1 = df.reset_index(drop = True)
    ph = ['InPlay', 'HitByPitch'] # 同じく変数です。
    kb = ['Strikeout', 'Walk'] # 同じく変数です。
    bunt = ['Bunt', "GroundBall"] #バントっていう変数
    df2 = df1.query('PitchCall == @ph or KorBB == @kb')
    
    ds = len(df2) #打席数
    ht = len(df2.query('PlayResult == @hit')) #安打数
    bb = len(df2.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    bu = len(df2.query('PlayResult == "Sacrifice"').query('TaggedHitType == @bunt')) #バント数
    if ds-bu != 0:
        obp = round((ht+bb)/(ds-bu), 3) #出塁率
    else:
        obp = np.nan #分母が0の時の出塁率
    if mc:
        return obp, ds-bu, ht+bb
    else:
        return obp
    
def SA(df, mc = False): #Slugging Average
    df1 = df.reset_index(drop = True)
    ph = ['InPlay', 'HitByPitch'] # 同じく変数です。
    kb = ['Strikeout', 'Walk'] # 同じく変数です。
    df2 = df1.query('PitchCall == @ph or KorBB == @kb')
    ds = len(df2) #打席数
    sg  = len(df2.query('PlayResult == "Single"'))  #単打数
    two = len(df2.query('PlayResult == "Double"'))  #2塁打数
    thr = len(df2.query('PlayResult == "Triple"'))  #3塁打数
    hr  = len(df2.query('PlayResult == "HomeRun"')) #本塁打数
    sc = len(df2.query('PlayResult == "Sacrifice"')) #犠牲打数
    bb = len(df2.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    if ds-sc-bb != 0:
        sa = round((sg + 2*two + 3*thr + 4*hr)/(ds-sc-bb), 3) #長打率
    else:
        sa = np.nan #分母が0の時の長打率
    if mc:
        return sa, ds-sc-bb, sg + 2*two + 3*thr + 4*hr
    else:
        return sa

def OPS(df): # On Base plus Slugging
    df1 = df.reset_index(drop = True)
    if OBP(df1, mc = True)[1] == 0:
        ops = SA(df1, mc = False)
    elif SA(df1, mc = True)[1] == 0:
        ops = OBP(df1, mc =False)
    else:
        ops = SA(df1, mc = False) + OBP(df1, mc = False)
    return round(ops, 3)


def IsoP(df): # Isolated Power
    return round(SA(df) - BA(df), 3)

def IsoD(df): # Isolated Discipline
    if str(OBP(df, mc = True)[1]) == 'nan' or str(BA(df, mc = True)[1]) == 'nan':
        isod = np.nan
    elif OBP(df, mc = True)[1] == 0:
        isod = -BA(df)
    elif BA(df, mc = True)[1] == 0:
        isod = OBP(df)
    else:
        isod = round(OBP(df,mc=False) - BA(df), 3)
    return isod

def BAPIP(df, mc = False): # Batting Average on Balls In Play
    hit = ["Single", "Double", "Triple", "HomeRun"] # hitっていう変数作ります。
   
    df1 = df.reset_index(drop = True)
    ph = ['InPlay', 'HitByPitch'] # 同じく変数です。
    kb = ['Strikeout', 'Walk'] # 同じく変数です。
    bunt = ['Bunt', "GroundBall"] #バントっていう変数
    df2 = df1.query('PitchCall == @ph or KorBB == @kb')

    ds = len(df2) #打席数
    ht = len(df2.query('PlayResult == @hit')) #安打数
    hr = len(df2.query('PlayResult == "HomeRun"')) #ホームラン数
    bb = len(df2.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    bu = len(df2.query('PlayResult == "Sacrifice" and TaggedHitType == @bunt')) #バント数
    kk = len(df2.query('KorBB == "Strikeout"')) #三振数
    
    if ds-bb - kk - hr - bu != 0:
        bapip = round((ht-hr) / (ds - bb - kk - hr - bu), 3)
    else:
        bapip = np.nan
    if mc:
        return bapip, ds - bb - kk - hr - bu, ht-hr
    else:
        return bapip

def wOBA(df, coef = [0.7, 0.9, 1.3, 1.6, 2.0]): # Weighted On Base Average
    df1 = df.reset_index(drop = True)
    ph = ['InPlay', 'HitByPitch'] # 同じく変数です。
    kb = ['Strikeout', 'Walk'] # 同じく変数です。
    bunt = ['Bunt', "GroundBall"] #バントっていう変数
    df2 = df1.query('PitchCall == @ph or KorBB == @kb')
    ds = len(df2) #打席数
    bb = len(df2.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    bu = len(df2.query('PlayResult == "Sacrifice"').query('TaggedHitType == @bunt')) #バント数
    sg  = len(df2.query('PlayResult == "Single"'))  #単打数
    two = len(df2.query('PlayResult == "Double"'))  #2塁打数
    thr = len(df2.query('PlayResult == "Triple"'))  #3塁打数
    hr  = len(df2.query('PlayResult == "HomeRun"')) #本塁打数
    
    if ds - bu != 0:
        woba = round((coef[0]*bb + coef[1]*sg + coef[2]*two + coef[3]*thr + coef[4]*hr) / (ds - bu), 3)
    else:
        woba = np.nan
    return woba

def SWING(df, mc = False, azo = 0, xrange = [-0.3, 0.3], zrange = [0.45, 1.05]):
# azoは, AllかZoneかOut-Swing％のどれを出すかってことです。
# 0だと普通の, 1だとZone-Swing%, 2だとOut-Swing%, 3以上だと全て出します。
    df1 = df.reset_index(drop = True)
    casw, masw, czsw, mzsw, cosw, mosw = np.zeros(6)
    
    nx, xx = xrange[0], xrange[1] 
    nz, xz = zrange[0], zrange[1]
    
    swing = ['InPlay', 'FoulBall','StrikeSwinging']
    masw, casw = len(df1), len(df1.query('PitchCall == @swing'))
    if 'PlateLocSide' in df1.columns:
        dfz = df1.query('@nx <= PlateLocSide <= @xx and @nz <= PlateLocHeight <= @xz')
        mzsw, czsw = len(dfz), len(dfz.query('PitchCall == @swing'))
        mosw, cosw = masw - mzsw, casw - czsw  

    
    msw = [masw, mzsw, mosw]
    csw = [casw, czsw, cosw]
    
    if masw == 0:
        sw = [np.nan, np.nan, np.nan]
    elif mzsw == 0:
        sw = [
        round(casw/masw* 100, 1) if masw != 0 else np.nan,  # maswが0でない場合のみ割り算
        np.nan,
        round(cosw/mosw* 100, 1) if mosw != 0 else np.nan   # moswが0でない場合のみ割り算
    ]
    elif mosw == 0:
        sw = [round(casw/masw* 100, 1), round(czsw/mzsw* 100, 1), np.nan]
    else:
        sw = [round(casw/masw* 100, 1), round(czsw/mzsw* 100, 1), round(cosw/mosw* 100, 1)]
        
    if azo not in [0, 1, 2]:
        return sw
    else:
        if mc:
            return sw[azo], msw[azo], csw[azo]
        else:
            return sw[azo]
    
def WHIFF(df, mc = False, azo = 0, xrange = [-0.3, 0.3], zrange = [0.45, 1.05]): 
    # strikezoneのxの範囲とzの範囲を指定
    # azoは all, zone, out の切り替え設定 0か1か2
    
    df1 = df.reset_index(drop = True)
    cawf, mawf, czwf, mzwf, cowf, mowf = np.zeros(6)
    
    nx, xx = xrange[0], xrange[1] 
    nz, xz = zrange[0], zrange[1]
    
    swing = ['InPlay', 'FoulBall','StrikeSwinging']
    mawf, cawf = len(df1.query('PitchCall == @swing')), len(df1.query('PitchCall == "StrikeSwinging"'))
    
    if 'PlateLocSide' in df1.columns:
        dfz = df1.query('@nx <= PlateLocSide <= @xx and @nz <= PlateLocHeight <= @xz') # ゾーンのz
        mzwf, czwf = len(dfz.query('PitchCall == @swing')), len(dfz.query('PitchCall == "StrikeSwinging"'))
        mowf, cowf = mawf - mzwf, cawf - czwf 
    
    mwf = [mawf, mzwf, mowf]
    cwf = [cawf, czwf, cowf]
    
    if mawf == 0:
        wf = [np.nan, np.nan, np.nan]
    elif mzwf == 0:
        wf = [round(cawf/mawf* 100, 1), np.nan, round(cowf/mowf* 100, 1)]
    elif mowf == 0:
        wf = [round(cawf/mawf* 100, 1), round(czwf/mzwf* 100, 1), np.nan]
    else:
        wf = [round(cawf/mawf* 100, 1), round(czwf/mzwf* 100, 1), round(cowf/mowf* 100, 1)]
        
    if azo not in [0, 1, 2]:
        return wf
    else:
        if mc:
            return wf[azo], mwf[azo], cwf[azo]
        else:
            return wf[azo]
        
def HardHit(df, es=140):
    df_es = df.query('TaggedHitType != "Bunt"').dropna(subset=['ExitSpeed'])
    if len(df_es):
        return len(df_es.query('ExitSpeed >= @es')) / len(df_es)
    else:
        return float('nan')
    
def gpf(df, mc = False): # goro per fly 
    df = df.query('TaggedHitType != "Bunt"')
    df1 = df.query('PitchCall == "InPlay"').query('0 < Angle <= 15')
    df2 = df.query('PitchCall == "InPlay"').query('Angle <= 0')
    df3 = df.query('PitchCall == "InPlay"').query('Angle > 15')
    r = np.array(df1.Distance)
    th = np.array(df1.Direction)
    g, f =len(df2), len(df3)
    for i in range(len(df1)):
        x = r[i] * np.cos(th[i])
        y = r[i] * np.sin(th[i])
        if (y <= x) and (y >= -x) and (y <= -x + 38.795) and (y >= x -38.795):
            g += 1
        else:
            f += 1
    if f != 0:
        if mc:
            return round(g/f, 2), f, g
        else:
            return round(g/f, 2)
    else:
        if mc:
            return f"{g}/{f}", f, g
        else:
            return f"{g}/{f}"

def gbpercent(df):
    df1 = df.query('PitchCall == "InPlay"')
    gb = len(df1.query('AutoHitType == "GroundBall"'))
    fb = len(df1.query('AutoHitType == "FlyBall"'))
    if gb + fb != 0:
        return round(gb/len(df1) * 100, 1)
    else:
        return np.nan

def fbpercent(df):
    df1 = df.query('PitchCall == "InPlay"')
    gb = len(df1.query('AutoHitType == "GroundBall"'))
    fb = len(df1.query('AutoHitType == "FlyBall"'))
    if gb + fb != 0:
        return round(fb/len(df1) * 100, 1)
    else:
        return np.nan

def changeba(Ba):
    if type(Ba) == str:
        return '-'
    if np.isnan(Ba):
        return '-'
    
    ba = round(round(Ba, 3)*1000)
    if ba >= 1000:
        return f'{ba//1000}{changeba((ba%1000)/1000)}'
    elif Ba < 0.01:
        return f'.00{str(ba)}'
    elif Ba < 0.1:
        return f'.0{str(ba)}'
    else:
        return f'.{str(ba)}'
    
def dasu(df):
    ph = ['InPlay', 'HitByPitch'] # 変数
    kb = ['Strikeout', 'Walk'] # 変数
    sc = len(df.query('PlayResult == "Sacrifice"')) #犠牲打数
    bb = len(df.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    return len(df.query('PitchCall == @ph or KorBB == @kb')) - sc - bb
    
def seki(df):
    ph = ['InPlay', 'HitByPitch'] # 変数
    kb = ['Strikeout', 'Walk'] # 変数
    return len(df.query('PitchCall == @ph or KorBB == @kb'))

def countpr(df, pr = 'Single'):
    ph = ['InPlay', 'HitByPitch'] # 変数
    kb = ['Strikeout', 'Walk'] # 変数
    if pr in kb:
        return len(df.query('KorBB == @pr'))
    elif pr == 'HitByPitch':
        return len(df.query('PitchCall == @pr'))
    else:
        return len(df.query('PitchCall == @ph or KorBB == @kb').query('PlayResult == @pr'))

def stl(df):
    if 'runevent' in df.columns:
        return len(df.query('runevent.str.contains("Steal", na=False)', engine = 'python').runevent) - \
            len(df.query('runevent.str.contains("StealOut", na=False)', engine = 'python').runevent), \
                len(df.query('runevent.str.contains("StealOut", na=False)', engine = 'python').runevent)
    elif "Steal" in df.columns:
        return len(df.query('Steal == "Steal"')), len(df.query('Steal == "StealOut"'))
    else:
        return 0, 0
    
def Kp(df, mc =False):
    ds = dasu(df)
    kk = len(df.query('KorBB == "Strikeout"'))
    if ds == 0:
        kp = np.nan
    else:
        kp = round(kk/ds, 3)
    if mc:
        return kp, ds, kk
    else:
        return kp


def strikeratio2(df,mc=False):
    df = df.query('runevent != "PickOff"')
    strike= ['InPlay', 'FoulBall','StrikeSwinging', 'StrikeCalled']
    df1 = df.query('PitchCall == @strike')
    sr = round(len(df1)/len(df) * 100, 1)
    if mc:
        return f'{sr} {len(df1)}/{len(df)}'
    else:
        return sr


def retband(df, item = "RelSpeed", kakko = False):
    if len(df) == 0:
        return '---'
    df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all', axis=1)
    if item not in df.describe().columns:
        return '---'
    result = df.describe()[item][['min','mean', 'max']]
    if len(df) == 1:
        if kakko:
            return '[' + str(round(result.min())) + ']'
        else:
            return round(result.min())
    n = round(result.min())
    x = round(result.max())
    mn = round(result.mean())
    if kakko:
        return '(' + str(n) +  '-' +  str(x) + ')' +'[' + str(mn) + ']'
    else:
        return str(n) +  '-' +  str(x) + '\n'+'[' + str(mn) + ']'
    
def fip(df1):
    hr =  len(df1.query('PlayResult == "HomeRun"')) #HR数
    kk = len(df1.query('KorBB == "Strikeout"'))#奪三振数
    bb = len(df1.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    inn = (len(df1.query('OutsOnPlay == 1')) + len(df1.query('OutsOnPlay == 2')) * 2 + len(df1.query('OutsOnPlay == 3'))) / 3 * 3 #投球回
    if inn != 0:
        fip = round((13 * hr + 3 * bb - 2 * kk) / inn + 3 , 2)
    else:
        fip = 99.99
    return fip

def tRA(df1):
    hr =  len(df1.query('PlayResult == "HomeRun"')) #HR数
    kk = len(df1.query('KorBB == "Strikeout"'))#奪三振数
    bb = len(df1.query('PitchCall == "HitByPitch" or KorBB == "Walk"')) #四死球数
    gb = len(df1.query('AutoHitType == "GroundBall"'))#ゴロ数
    lb = len(df1.query('AutoHitType == "LineDrive"'))#ライナー数
    pb = len(df1.query('AutoHitType == "Popup"'))#打ち上げ数
    fb = len(df1.query('AutoHitType == "FlyBall"'))#フライ数
    RuEx = 0.3 * bb + -0.11 * kk + 1.41 * hr + 0.03 * gb + -0.12 * pb + 0.12 * fb + 0.33 * lb
    OuEx = kk + 0.75 * gb + -0.99 * pb + 0.71 * fb + 0.26 * lb
    tRA = round(27 * RuEx /OuEx , 2)
    return tRA

