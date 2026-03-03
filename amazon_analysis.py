#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon February 2026 Sales Analysis Report Generator
自动分析亚马逊二月销售报告，生成HTML可视化报告
"""

import os
import re
import csv
import json
import urllib.request
from datetime import datetime
from collections import defaultdict
from html import escape

# ==================== 配置 ====================
REPORTS_DIR = "amazon/2026FebReports"
ALL_COUNTRIES = ["DE", "IT", "FR", "ES", "UK"]  # 显示顺序
EU4_CURRENCY = "EUR"
UK_CURRENCY = "GBP"

# 备用汇率（API失败时使用）
FALLBACK_RATES = {
    "EUR_USD": 1.08,
    "GBP_USD": 1.27
}

# ==================== 汇率获取 ====================
def fetch_exchange_rates():
    """获取当前汇率"""
    print("正在获取汇率...")
    rates = {"EUR_USD": None, "GBP_USD": None}
    
    try:
        with urllib.request.urlopen("https://api.frankfurter.app/latest?from=USD", timeout=10) as response:
            data = json.loads(response.read().decode())
            usd_to_eur = data["rates"]["EUR"]
            rates["EUR_USD"] = 1 / usd_to_eur
            rates["GBP_USD"] = data["rates"]["GBP"] / usd_to_eur
    except Exception as e:
        print(f"汇率API调用失败: {e}, 使用备用汇率")
        rates["EUR_USD"] = FALLBACK_RATES["EUR_USD"]
        rates["GBP_USD"] = FALLBACK_RATES["GBP_USD"]
    
    print(f"汇率: EUR→USD: {rates['EUR_USD']:.4f}, GBP→USD: {rates['GBP_USD']:.4f}")
    return rates

# ==================== 工具函数 ====================
def parse_european_number(value):
    """解析欧洲格式数字: 1.234,56 -> 1234.56"""
    if not value or value == "":
        return 0.0
    value = str(value).strip()
    # 处理 "<5%" 这样的格式
    if '<' in value:
        return 0.0
    # 处理百分比格式 "3.95%" -> 3.95
    if '%' in value:
        value = value.replace('%', '')
        try:
            return float(value)
        except:
            return 0.0
    value = re.sub(r'[€£$\s]', '', value)
    if ',' in value and '.' in value:
        if value.find(',') < value.find('.'):
            value = value.replace(',', '')
        else:
            value = value.replace('.', '').replace(',', '.')
    elif ',' in value:
        if len(value.split(',')[-1]) == 2:
            value = value.replace(',', '.')
        else:
            value = value.replace(',', '')
    return float(value) if value else 0.0

def parse_currency_amount(value):
    """解析货币金额"""
    return parse_european_number(value)

# ==================== 数据读取 ====================
def load_business_report(country):
    """读取Business Report，返回产品列表和汇总数据"""
    filepath = os.path.join(REPORTS_DIR, f"{country}BusinessReport-02-3-26.csv")
    if not os.path.exists(filepath):
        print(f"警告: 找不到文件 {filepath}")
        return [], {'impressions': 0, 'sessions': 0, 'orders': 0, 'conversion_rate': 0}
    
    products = []
    total_sessions = 0
    total_conversion_rate = 0
    product_count = 0
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        sku_idx = None
        title_idx = None
        qty_idx = None
        sales_idx = None
        sessions_idx = None
        conv_rate_idx = None
        
        for i, h in enumerate(headers):
            h_lower = h.lower()
            if 'sku' in h_lower and sku_idx is None:
                sku_idx = i
            elif ('标题' in h or 'title' in h_lower) and title_idx is None:
                title_idx = i
            elif h == '已订购商品数量' or (h_lower == 'ordered' and 'b2b' not in h_lower):
                if qty_idx is None:
                    qty_idx = i
            elif h == '已订购商品销售额' or (h_lower == 'sales' and 'b2b' not in h_lower and 'refund' not in h_lower):
                if sales_idx is None:
                    sales_idx = i
            elif '会话数' in h and sessions_idx is None:
                sessions_idx = i
            elif '商品会话百分比' in h and conv_rate_idx is None:
                conv_rate_idx = i
        
        for row in reader:
            if len(row) > max(sku_idx or 0, qty_idx or 0, sales_idx or 0):
                sku = row[sku_idx].strip() if sku_idx is not None else ""
                title = row[title_idx].strip() if title_idx is not None else ""
                qty = parse_european_number(row[qty_idx]) if qty_idx is not None else 0
                sales = parse_currency_amount(row[sales_idx]) if sales_idx is not None else 0
                
                # 累加流量
                if sessions_idx is not None and len(row) > sessions_idx:
                    session_val = parse_european_number(row[sessions_idx])
                    total_sessions += session_val
                
                # 累加转化率
                if conv_rate_idx is not None and len(row) > conv_rate_idx:
                    cr = parse_european_number(row[conv_rate_idx])
                    if cr > 0:
                        total_conversion_rate += cr
                        product_count += 1
                
                if sku:
                    products.append({
                        'country': country,
                        'sku': sku,
                        'title': title,
                        'quantity': qty,
                        'sales': sales
                    })
    
    # 计算平均转化率
    avg_conversion_rate = total_conversion_rate / product_count if product_count > 0 else 0
    
    summary = {
        'impressions': 0,  # 页面浏览量
        'sessions': total_sessions,  # 会话数（流量）
        'orders': sum(p['quantity'] for p in products),
        'conversion_rate': avg_conversion_rate
    }
    
    return products, summary

def is_uk_transaction_format(filepath):
    """检测是否为UK汇总表格式"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline()
        return '求和项' in first_line or 'Sum' in first_line

def load_transaction_report(country):
    """读取Transaction Report"""
    filepath = os.path.join(REPORTS_DIR, f"{country}2026Feb1-2026Feb28CustomTransaction.csv")
    if not os.path.exists(filepath):
        print(f"警告: 找不到文件 {filepath}")
        return {'orders': 0, 'refunds': 0, 'sales': 0, 'fees': 0, 'total': 0}
    
    is_uk_format = is_uk_transaction_format(filepath)
    
    if is_uk_format:
        return load_uk_transaction_format(filepath)
    else:
        return load_eu4_transaction_format(filepath)

def load_uk_transaction_format(filepath):
    """读取UK汇总表格式"""
    result = {'orders': 0, 'refunds': 0, 'sales': 0, 'fees': 0, 'total': 0}
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 10:
                continue
            if '总计' in row[0] or 'Total' in row[0] or row[0].strip() == '':
                continue
            try:
                qty = parse_european_number(row[1]) if row[1] else 0
                sales = parse_european_number(row[2]) if row[2] else 0
                fees = parse_european_number(row[5]) + parse_european_number(row[6])
                total = parse_european_number(row[9]) if row[9] else 0
                
                if sales > 0:
                    result['orders'] += qty
                    result['sales'] += sales
                    result['fees'] += abs(fees)
                elif total < 0:
                    result['refunds'] += abs(total)
            except:
                pass
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if '总计' in str(row[0]) or 'Total' in str(row[0]):
                if len(row) >= 10:
                    result['sales'] = parse_european_number(row[2]) if row[2] else 0
                    result['total'] = parse_european_number(row[9]) if row[9] else 0
    
    return result

def load_eu4_transaction_format(filepath):
    """读取EU4详细交易格式"""
    result = {'orders': 0, 'refunds': 0, 'sales': 0, 'fees': 0, 'total': 0}
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        # 跳过描述性行，找到实际header
        headers = next(reader)
        while headers and len(headers) < 5:
            headers = next(reader)
        
        type_idx = None
        total_idx = None
        
        for i, h in enumerate(headers):
            h_zh = h.lower()
            if 'typ' in h_zh or 'tipo' in h_zh or 'type' in h_zh:
                type_idx = i
            elif 'total' in h_zh:
                total_idx = i
        
        for row in reader:
            if len(row) <= max(type_idx or 0, total_idx or 0):
                continue
            
            trans_type = row[type_idx].lower() if type_idx is not None else ""
            total = parse_currency_amount(row[total_idx]) if total_idx is not None else 0
            
            # 订单关键词（多语言）
            if any(kw in trans_type for kw in ['bestellung', 'pedido', 'order', 'commande', 'ordine']):
                if total > 0:
                    result['orders'] += 1
                    result['sales'] += total
            # 退款关键词
            elif any(kw in trans_type for kw in ['erstattung', 'reembolso', 'refund', 'rimborso']):
                if total < 0:
                    result['refunds'] += abs(total)
            # 服务费关键词
            elif any(kw in trans_type for kw in ['geb', 'tarifa', 'fee', 'frais', 'servizio', 'servicegeb']):
                if total < 0:
                    result['fees'] += abs(total)
            
            if total != 0:
                result['total'] += total
    
    return result

def load_returns_report():
    """读取Returns Report"""
    filepath = os.path.join(REPORTS_DIR, "2026FebReturns.csv")
    if not os.path.exists(filepath):
        print(f"警告: 找不到文件 {filepath}")
        return []
    
    returns = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        sku_idx = None
        product_idx = None
        reason_idx = None
        status_idx = None
        order_id_idx = None
        
        for i, h in enumerate(headers):
            h_lower = h.lower().replace('"', '')
            if h_lower == 'sku':
                sku_idx = i
            elif 'product' in h_lower or '名称' in h:
                product_idx = i
            elif 'reason' in h_lower:
                reason_idx = i
            elif 'status' in h_lower:
                status_idx = i
            elif 'order' in h_lower:
                order_id_idx = i


        
        for row in reader:
            if len(row) > max(sku_idx or 0, reason_idx or 0):
                returns.append({
                    'sku': row[sku_idx].strip() if sku_idx is not None else "",
                    'product': row[product_idx][:50] + "..." if product_idx and len(row[product_idx]) > 50 else (row[product_idx] if product_idx else ""),
                    'reason': row[reason_idx].strip() if reason_idx is not None else "",
                    'status': row[status_idx].strip() if status_idx is not None else "",
                    'order_id': row[order_id_idx].strip() if order_id_idx is not None else ""
                })
    
    return returns

# ==================== 广告数据处理 ====================
def load_ads_data():
    """读取广告报表"""
    filepath = os.path.join(REPORTS_DIR, "Campaign_Mar_3_2026.csv")
    if not os.path.exists(filepath):
        print(f"警告: 找不到广告文件 {filepath}")
        return {}
    
    ads_by_country = defaultdict(lambda: {
        'impressions': 0, 'clicks': 0, 'spend': 0, 'sales': 0, 
        'orders': 0, 'campaigns': 0, 'enabled_campaigns': 0
    })
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # 找到关键列
        country_idx = None
        status_idx = None
        spend_idx = None
        sales_idx = None
        clicks_idx = None
        impressions_idx = None
        orders_idx = None
        ctr_idx = None
        
        for i, h in enumerate(headers):
            h_cn = h.strip().replace('﻿', '')
            if '国家' in h_cn:
                country_idx = i
            elif '状态' in h_cn and '广告活动状态' not in h_cn:
                status_idx = i
            elif '总成本' in h_cn and '转换' not in h_cn:
                spend_idx = i
            elif '销售额' in h_cn and '广告活动预算' not in h_cn and '转换' not in h_cn:
                sales_idx = i
            elif '点击量' in h_cn and clicks_idx is None:
                clicks_idx = i
            elif '展示量' in h_cn and impressions_idx is None:
                impressions_idx = i
            elif '购买量' in h_cn and orders_idx is None:
                orders_idx = i
            elif '点击率' in h_cn and ctr_idx is None:
                ctr_idx = i
        
        for row in reader:
            if len(row) <= max(country_idx or 0, spend_idx or 0, sales_idx or 0):
                continue
            
            # 解析国家
            country_raw = row[country_idx].strip() if country_idx is not None else ""
            country_map = {'德国': 'DE', '意大利': 'IT', '法国': 'FR', '西班牙': 'ES', '英国': 'UK'}
            country = country_map.get(country_raw, None)
            
            if country is None:
                continue
            
            # 解析数值
            spend = parse_currency_amount(row[spend_idx]) if spend_idx is not None else 0
            sales = parse_currency_amount(row[sales_idx]) if sales_idx is not None else 0
            clicks = parse_european_number(row[clicks_idx]) if clicks_idx is not None else 0
            impressions = parse_european_number(row[impressions_idx]) if impressions_idx is not None else 0
            orders = parse_european_number(row[orders_idx]) if orders_idx is not None else 0
            # CTR是直接读取的值（如0.0071表示0.71%）
            ctr_val = parse_european_number(row[ctr_idx]) if ctr_idx is not None else 0
            
            status = row[status_idx].strip() if status_idx is not None else ""
            is_enabled = '已启用' in status or 'Enabled' in status
            
            # 累加点击和展示用于后续计算加权CTR
            ads_by_country[country]['spend'] += spend
            ads_by_country[country]['sales'] += sales
            ads_by_country[country]['clicks'] += clicks
            ads_by_country[country]['impressions'] += impressions
            ads_by_country[country]['orders'] += orders
            ads_by_country[country]['campaigns'] += 1
            if is_enabled:
                ads_by_country[country]['enabled_campaigns'] += 1
    
    return dict(ads_by_country)

# ==================== 数据处理 ====================
def process_business_data():
    """处理Business Report数据 - 按五国分别统计"""
    print("\n=== 读取Business Reports ===")
    
    country_data = {}
    all_products = defaultdict(lambda: {'quantity': 0, 'sales': 0, 'title': '', 'countries': []})
    
    for country in ALL_COUNTRIES:
        products, summary = load_business_report(country)
        total_qty = summary['orders']
        total_sales = sum(p['sales'] for p in products)
        
        country_data[country] = {
            'total_qty': total_qty,
            'total_sales': total_sales,
            'sessions': summary['sessions'],
            'conversion_rate': summary['conversion_rate']
        }
        
        # 合并产品（用于全球排行）
        for p in products:
            key = p['sku']
            all_products[key]['quantity'] += p['quantity']
            all_products[key]['sales'] += p['sales']
            all_products[key]['title'] = p['title']
            all_products[key]['countries'].append(country)
        
        currency = 'GBP' if country == 'UK' else 'EUR'
        print(f"  {country}: {total_qty} 件, {currency}{total_sales:,.2f}, 流量:{summary['sessions']:.0f}")
    
    return {
        'by_country': country_data,
        'all_products': all_products
    }

def process_transaction_data():
    """处理Transaction Report数据 - 按五国分别统计"""
    print("\n=== 读取Transaction Reports ===")
    
    country_trans = {}
    
    for country in ALL_COUNTRIES:
        trans = load_transaction_report(country)
        country_trans[country] = trans
        currency = 'GBP' if country == 'UK' else 'EUR'
        print(f"  {country}: 订单{trans['orders']}, 销售额{currency}{trans['sales']:,.2f}, 退款{currency}{trans['refunds']:,.2f}")
    
    return country_trans

def process_returns_data():
    """处理退货数据 - 按国家和SKU分别统计"""
    print("\n=== 读取Returns Report ===")
    
    returns = load_returns_report()
    
    # 按SKU汇总（包含主要退货原因）
    sku_returns = defaultdict(lambda: {'count': 0, 'reasons': defaultdict(int)})
    reason_dist = defaultdict(int)
    status_dist = defaultdict(int)
    country_returns = defaultdict(int)
    
    # 从order-id解析国家
    for r in returns:
        sku = r['sku']
        reason = r['reason']
        status = r['status']
        order_id = r.get('order_id', '')
        
        # 尝试从order-id或sku推断国家
        country = 'Unknown'
        if 'UK' in order_id[:3] or '171-' in order_id or '404-' in order_id:
            country = 'UK'
        elif '028-' in order_id or '302-' in order_id or '304-' in order_id or '305-' in order_id or '306-' in order_id:
            country = 'DE'
        elif '406-' in order_id or '407-' in order_id:
            country = 'ES'
        elif '408-' in order_id:
            country = 'FR'
        elif '026-' in order_id:
            country = 'IT'
        
        # 检查SKU前缀
        if 'UK' in sku:
            country = 'UK'
        elif sku.startswith('EU '):
            pass  # 保持原判断
        
        country_returns[country] += 1
        
        sku_returns[sku]['count'] += 1
        if reason:
            sku_returns[sku]['reasons'][reason] += 1
            reason_dist[reason] += 1
        status_dist[status] += 1
    
    total_returns = len(returns)
    
    # 处理每个SKU的主要退货原因
    top_returns = []
    for sku, data in sku_returns.items():
        main_reason = max(data['reasons'].items(), key=lambda x: x[1])[0] if data['reasons'] else ''
        top_returns.append({
            'sku': sku,
            'count': data['count'],
            'main_reason': main_reason
        })
    top_returns = sorted(top_returns, key=lambda x: x['count'], reverse=True)[:10]
    
    print(f"总退货: {total_returns} 件")
    print(f"各国退货: {dict(country_returns)}")
    print(f"退货原因分布: {dict(reason_dist)}")
    
    return {
        'total': total_returns,
        'by_sku': sku_returns,
        'top_returns': top_returns,
        'by_country': dict(country_returns),
        'reason_dist': reason_dist,
        'status_dist': status_dist
    }

# ==================== HTML报告生成 ====================
def generate_html_report(business_data, trans_data, returns_data, ads_data, rates):
    """生成HTML报告"""
    
    # 各国销售数据
    country_names = {'DE': '🇩🇪 德国', 'IT': '🇮🇹 意大利', 'FR': '🇫🇷 法国', 'ES': '🇪🇸 西班牙', 'UK': '🇬🇧 英国'}
    
    # 计算全球总计
    total_sales_eur = sum(d['total_sales'] for c, d in business_data['by_country'].items() if c != 'UK')
    total_sales_gbp = business_data['by_country'].get('UK', {}).get('total_sales', 0)
    total_qty = sum(d['total_qty'] for d in business_data['by_country'].values())
    
    total_sales_usd = total_sales_eur * rates['EUR_USD'] + total_sales_gbp * rates['GBP_USD']
    
    # 各国退货率
    returns_by_country = returns_data.get('by_country', {})
    
    # 生成五国概览表格（详细版）
    country_overview = ""
    global_sessions = 0
    global_qty = 0
    global_sales_eur = 0
    global_sales_gbp = 0
    global_ads_spend_eur = 0
    global_ads_spend_gbp = 0
    
    for country in ALL_COUNTRIES:
        data = business_data['by_country'].get(country, {'total_qty': 0, 'total_sales': 0, 'sessions': 0, 'conversion_rate': 0})
        ads = ads_data.get(country, {'spend': 0})
        
        qty = data['total_qty']
        sales = data['total_sales']
        sessions = data.get('sessions', 0)
        conv_rate = data.get('conversion_rate', 0)
        ads_spend = ads.get('spend', 0)
        
        # 计算客单价
        aov = sales / qty if qty > 0 else 0
        
        # 计算ROI（总销售额/广告支出）
        roi = sales / ads_spend if ads_spend > 0 else 0
        
        # 转换为美元
        sales_usd = sales * rates['EUR_USD'] if country != 'UK' else sales * rates['GBP_USD']
        ads_spend_usd = ads_spend * rates['EUR_USD'] if country != 'UK' else ads_spend * rates['GBP_USD']
        
        currency = 'GBP' if country == 'UK' else 'EUR'
        symbol = '£' if country == 'UK' else '€'
        
        global_sessions += sessions
        global_qty += qty
        if country == 'UK':
            global_sales_gbp += sales
            global_ads_spend_gbp += ads_spend
        else:
            global_sales_eur += sales
            global_ads_spend_eur += ads_spend
        
        country_overview += f"""<tr>
            <td>{country_names.get(country, country)}</td>
            <td style="text-align:right">{int(sessions):,}</td>
            <td style="text-align:right">{symbol}{sales:,.2f} (${sales_usd:,.2f})</td>
            <td style="text-align:right">{int(qty)}</td>
            <td style="text-align:right">{symbol}{aov:,.2f}</td>
            <td style="text-align:right">{conv_rate:.1f}%</td>
            <td style="text-align:right">{symbol}{ads_spend:,.2f} (${ads_spend_usd:,.2f})</td>
            <td style="text-align:right">{roi:.2f}</td>
        </tr>"""
    
    # 全球总计
    total_sales_usd = global_sales_eur * rates['EUR_USD'] + global_sales_gbp * rates['GBP_USD']
    total_ads_spend_usd = global_ads_spend_eur * rates['EUR_USD'] + global_ads_spend_gbp * rates['GBP_USD']
    global_aov = (global_sales_eur + global_sales_gbp * rates['GBP_USD']) / global_qty if global_qty > 0 else 0
    global_roi = total_sales_usd / total_ads_spend_usd if total_ads_spend_usd > 0 else 0
    
    conv_rates = [business_data['by_country'].get(c, {}).get('conversion_rate', 0) for c in ALL_COUNTRIES]
    global_conv_rate = sum(conv_rates) / len(conv_rates) if conv_rates else 0
    
    country_overview += f"""<tr style="font-weight:bold;background:#f0f4ff;">
        <td>🌍 全球总计</td>
        <td style="text-align:right">{int(global_sessions):,}</td>
        <td style="text-align:right">${total_sales_usd:,.2f}</td>
        <td style="text-align:right">{int(global_qty)}</td>
        <td style="text-align:right">${global_aov:,.2f}</td>
        <td style="text-align:right">{global_conv_rate:.1f}%</td>
        <td style="text-align:right">${total_ads_spend_usd:,.2f}</td>
        <td style="text-align:right">{global_roi:.2f}</td>
    </tr>"""
    
    # 构建产品列表（带各国销量）- 从business_data中获取
    # 由于load_business_report返回变化，这里重新加载产品数据
    country_qty = {c: {} for c in ALL_COUNTRIES}
    for country in ALL_COUNTRIES:
        products, _ = load_business_report(country)  # 忽略summary
        for p in products:
            sku = p['sku']
            if sku not in country_qty[country]:
                country_qty[country][sku] = 0
            country_qty[country][sku] += p['quantity']
    
    all_skus = set()
    for c in ALL_COUNTRIES:
        all_skus.update(country_qty[c].keys())
    
    product_list = []
    for sku in all_skus:
        qty_by_country = {c: country_qty[c].get(sku, 0) for c in ALL_COUNTRIES}
        total_qty = sum(qty_by_country.values())
        product_list.append({
            'sku': sku,
            'qty_by_country': qty_by_country,
            'total_qty': total_qty
        })
    
    top_products = sorted(product_list, key=lambda x: x['total_qty'], reverse=True)[:12]
    
    # 退货原因分布
    reason_html = ""
    for reason, count in sorted(returns_data['reason_dist'].items(), key=lambda x: x[1], reverse=True):
        pct = count / returns_data['total'] * 100
        reason_html += f"<tr><td>{escape(reason)}</td><td style='text-align:right'>{count}</td><td style='text-align:right'>{pct:.0f}%</td></tr>"
    
    # 退货产品排行（含主要退货原因）
    returns_html = ""
    for item in returns_data['top_returns'][:10]:
        returns_html += f"<tr><td><code>{escape(item['sku'])}</code></td><td style='text-align:right'>{item['count']}</td><td>{escape(item['main_reason'])}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>亚马逊二月销售报告 (2026)</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 16px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #1a1a2e; text-align: center; margin-bottom: 8px; font-size: 24px; }}
        .subtitle {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 13px; }}
        .card {{ background: white; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card-title {{ font-size: 15px; font-weight: 600; color: #1a1a2e; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fc; font-weight: 600; color: #555; font-size: 12px; }}
        td {{ font-size: 13px; }}
        tr:hover {{ background: #f8f9fc; }}
        .badge {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: 500; text-align: center; min-width: 50px; }}
        .text-right {{ text-align: right; }}
        .badge-eu4 {{ background: #e3f2fd; color: #1565c0; }}
        .badge-uk {{ background: #fff3e0; color: #e65100; }}
        .total-row {{ background: #f0f4ff; font-weight: 600; }}
        code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 亚马逊二月销售报告</h1>
        <p class="subtitle">Amazon February 2026 | 汇率: EUR→USD {rates['EUR_USD']:.2f} GBP→USD {rates['GBP_USD']:.2f}</p>
        
        <!-- 销售概览 - 五国详细表格 -->
        <div class="card">
            <div class="card-title">💰 各国核心数据 Country Overview</div>
            <table>
                <thead>
                    <tr>
                        <th>国家</th>
                        <th style="text-align:right">流量</th>
                        <th style="text-align:right">销售额</th>
                        <th style="text-align:right">订单量</th>
                        <th style="text-align:right">客单价</th>
                        <th style="text-align:right">转化率</th>
                        <th style="text-align:right">广告费用</th>
                        <th style="text-align:right">ROI</th>
                    </tr>
                </thead>
                <tbody>
                    {country_overview}
                </tbody>
            </table>
        </div>
        
        <!-- 产品销售排行 -->
        <div class="card">
            <div class="card-title">🏆 产品销量排行 Top Products</div>
            <table>
                <thead>
                    <tr><th>#</th><th>SKU</th><th style="text-align:right">DE</th><th style="text-align:right">IT</th><th style="text-align:right">FR</th><th style="text-align:right">ES</th><th style="text-align:right">UK</th><th style="text-align:right">总计</th></tr>
                </thead>
                <tbody>
"""
    
    for i, p in enumerate(top_products, 1):
        q = p['qty_by_country']
        html += f"""                    <tr><td>{i}</td><td><code>{escape(p['sku'])}</code></td><td style="text-align:right">{int(q.get('DE',0))}</td><td style="text-align:right">{int(q.get('IT',0))}</td><td style="text-align:right">{int(q.get('FR',0))}</td><td style="text-align:right">{int(q.get('ES',0))}</td><td style="text-align:right">{int(q.get('UK',0))}</td><td style="text-align:right"><strong>{int(p['total_qty'])}</strong></td></tr>
"""
    
    html += f"""                </tbody>
            </table>
        </div>
        
        <!-- 广告分析 -->
        <div class="card">
            <div class="card-title">📢 广告分析 Ads</div>
"""
    
    # 广告数据按国家汇总
    ads_html = ""
    total_ads_spend = 0
    total_ads_sales = 0
    total_ads_clicks = 0
    total_ads_impressions = 0
    total_ads_orders = 0
    
    # 各国总销售额（用于计算整体ROI）
    total_sales_by_country = business_data['by_country']
    total_ads_spend_eur = 0
    total_ads_spend_gbp = 0
    total_all_sales_eur = 0
    total_all_sales_gbp = 0
    
    for country in ALL_COUNTRIES:
        ads = ads_data.get(country, {})
        spend = ads.get('spend', 0)
        biz_sales = total_sales_by_country.get(country, {}).get('total_sales', 0)
        
        # 计算整体ROI = 总销售额 / 广告支出
        roi = biz_sales / spend if spend > 0 else 0
        acos = (spend / ads.get('sales', 0) * 100) if ads.get('sales', 0) > 0 else 0
        ctr = (ads.get('clicks', 0) / ads.get('impressions', 0) * 100) if ads.get('impressions', 0) > 0 else 0
        cvr = (ads.get('orders', 0) / ads.get('clicks', 0) * 100) if ads.get('clicks', 0) > 0 else 0
        
        if country == 'UK':
            total_ads_spend_gbp += spend
            total_all_sales_gbp += biz_sales
        else:
            total_ads_spend_eur += spend
            total_all_sales_eur += biz_sales
        
        symbol = '£' if country == 'UK' else '€'
        
        ads_html += f"""<tr>
            <td>{country_names.get(country, country)}</td>
            <td style="text-align:right">{symbol}{spend:,.2f}</td>
            <td style="text-align:right">{symbol}{biz_sales:,.2f}</td>
            <td style="text-align:right">{roi:.2f}</td>
            <td style="text-align:right">{ctr:.2f}%</td>
            <td style="text-align:right">{cvr:.2f}%</td>
            <td style="text-align:right">{acos:.2f}%</td>
        </tr>"""
    
    # 全球汇总（转换为欧元）
    total_ads_spend_usd = total_ads_spend_eur + total_ads_spend_gbp * rates['GBP_USD']
    total_all_sales_usd = total_all_sales_eur + total_all_sales_gbp * rates['GBP_USD']
    global_roi = total_all_sales_usd / total_ads_spend_usd if total_ads_spend_usd > 0 else 0
    global_acos = (total_ads_spend_usd / (ads_data.get('DE',{}).get('sales',0)*0 + ads_data.get('UK',{}).get('sales',0)*0) * 100) if 0 else 0
    global_ctr = (sum(d.get('clicks',0) for d in ads_data.values()) / sum(d.get('impressions',0) for d in ads_data.values()) * 100) if sum(d.get('impressions',0) for d in ads_data.values()) > 0 else 0
    global_cvr = (sum(d.get('orders',0) for d in ads_data.values()) / sum(d.get('clicks',0) for d in ads_data.values()) * 100) if sum(d.get('clicks',0) for d in ads_data.values()) > 0 else 0
    
    ads_html += f"""<tr style="font-weight:bold;background:#f0f4ff;">
        <td>🌍 全球总计</td>
        <td style="text-align:right">€{total_ads_spend_usd:,.2f}</td>
        <td style="text-align:right">€{total_all_sales_usd:,.2f}</td>
        <td style="text-align:right">{global_roi:.2f}</td>
        <td style="text-align:right">{global_ctr:.2f}%</td>
        <td style="text-align:right">{global_cvr:.2f}%</td>
        <td style="text-align:right">-</td>
    </tr>"""
    
    # 删除旧的重复代码
    html += f"""            <table>
                <thead>
                    <tr>
                        <th>国家</th>
                        <th style="text-align:right">广告支出</th>
                        <th style="text-align:right">总销售额</th>
                        <th style="text-align:right">整体ROI</th>
                        <th style="text-align:right">CTR</th>
                        <th style="text-align:right">转化率</th>
                        <th style="text-align:right">ACOS</th>
                    </tr>
                </thead>
                <tbody>
                    {ads_html}
                </tbody>
            </table>
        </div>
        
        <!-- 退货分析 -->
        <div class="card">
            <div class="card-title">🔄 退货分析 Returns</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                <div>
                    <div class="card-title" style="font-size:14px;">📦 退货产品</div>
                    <table>
                        <thead>
                            <tr><th>SKU</th><th style="text-align:right">退货数</th><th>主要原因</th></tr>
                        </thead>
                        <tbody>
                            {returns_html}
                        </tbody>
                    </table>
                </div>
                <div>
                    <div class="card-title">📈 退货原因</div>
                    <table>
                        <thead>
                            <tr><th>原因</th><th style="text-align:right">数量</th><th style="text-align:right">占比</th></tr>
                        </thead>
                        <tbody>
                            {reason_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <footer style="text-align: center; padding: 12px; color: #888; font-size: 11px;">
            amazon_analysis.py | Amazon Seller Central
        </footer>
    </div>
</body>
</html>
"""
    
    output_file = "amazon_report_2026Feb.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 报告已生成: {output_file}")
    return output_file

# ==================== 主程序 ====================
def main():
    print("=" * 50)
    print("亚马逊二月销售报告分析工具")
    print("Amazon February 2026 Sales Analysis")
    print("=" * 50)
    
    rates = fetch_exchange_rates()
    business_data = process_business_data()
    trans_data = process_transaction_data()
    returns_data = process_returns_data()
    ads_data = load_ads_data()
    output_file = generate_html_report(business_data, trans_data, returns_data, ads_data, rates)
    
    print("\n" + "=" * 50)
    print("分析完成!")
    print("=" * 50)
    
    return output_file

if __name__ == "__main__":
    main()
