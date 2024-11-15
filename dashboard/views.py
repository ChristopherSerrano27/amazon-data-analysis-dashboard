from math import log
import plotly.express as px
from django.shortcuts import render
from main.views import auth0_login_required
from .utils import import_and_clean_data
from django.http import JsonResponse
from main.views import get_user_roles
import requests
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# Función para verificar si la URL de la imagen es válida
def is_image_valid(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code == 200  # Si el código de estado es 200, la imagen es válida
    except requests.exceptions.RequestException:
        return False  # En caso de error, la URL no es válida

@auth0_login_required
def general_dashboard(request):
    # Importar y limpiar los datos
    df_clean = import_and_clean_data(data_folder='./dataset')

    if df_clean is None or df_clean.empty:
        return JsonResponse({"error": "No se pudo procesar los archivos o los archivos están vacíos."})

    # Asegurarse de que las calificaciones estén dentro del rango [1, 5]
    df_clean['ratings'] = df_clean['ratings'].apply(lambda x: min(max(x, 1), 5))

    # Calcular el total de productos y la distribución de categorías
    total_products = len(df_clean)
    category_counts = df_clean['main_category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']

    # Crear gráficos
    fig_category = px.bar(category_counts, x='Category', y='Count', title='Cantidad de Productos por Categoria')
    fig_ratings = px.histogram(df_clean, x='ratings', nbins=20, title='Distribución de Calificaciones')
    fig_price = px.histogram(df_clean, x='actual_price', nbins=20, title='Distribución de Precios')
    fig_discount_price = px.histogram(df_clean, x='discount_price', nbins=20, title='Distribución de Precios con Descuento')
    fig_reviews = px.histogram(df_clean, x='no_of_ratings', nbins=20, title='Distribución del Número de Reseñas')

    top_categories_reviews = df_clean.groupby('main_category')['no_of_ratings'].sum().sort_values(ascending=False).head(10)
    fig_category_top_reviews = px.bar(top_categories_reviews, x=top_categories_reviews.index, y=top_categories_reviews, title='Categorías con más Reseñas')

    top_discounted_categories = df_clean.groupby('main_category')['discount_price'].sum().sort_values(ascending=False).head(10)
    fig_category_top_discounts = px.bar(top_discounted_categories, x=top_discounted_categories.index, y=top_discounted_categories, title='Categorías con el Mayor Descuento')

    category_avg_price = df_clean.groupby('main_category')['actual_price'].mean().reset_index()
    fig_category_avg_price = px.bar(category_avg_price, x='main_category', y='actual_price', title='Precio Promedio por Categoría')

    ### Sección 3: Cálculo de rentabilidad
    # Calcular la rentabilidad en dólares y en porcentaje
    df_clean['profitability_usd'] = (df_clean['actual_price'] - df_clean['discount_price']) * df_clean['ratings']
    
    # Rentabilidad en porcentaje, basada en el precio original (no con descuento)
    df_clean['profitability_percent'] = (
        (df_clean['profitability_usd'] / df_clean['actual_price'].replace(0, 1)) * 100
    )

    # Filtrar los productos con la mayor rentabilidad
    top_profitability_products = df_clean.sort_values(by='profitability_usd', ascending=False).drop_duplicates(subset=['name']).head(3)

    # Preparar datos para la sección de "Productos con Mayor Rentabilidad"
    profitability_products = top_profitability_products[['name', 'main_category', 'ratings', 'discount_price', 'actual_price', 'no_of_ratings', 'image', 'link']].to_dict(orient='records')

    for product in profitability_products:
        image_url = product.get('image', '')
        if not image_url or not is_image_valid(image_url):
            product['image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='

    ### Sección 4: Mejores productos (más de 500 reseñas)
    top_products = df_clean[df_clean['no_of_ratings'] >= 500]
    # Los mejores productos se ordenan por calificación alta y buen descuento
    top_products = top_products.sort_values(by=['ratings', 'discount_price'], ascending=[False, False]).drop_duplicates(subset=['name']).head(3)

    best_products = top_products[['name', 'main_category', 'ratings', 'discount_price', 'actual_price', 'no_of_ratings', 'image', 'link']].to_dict(orient='records')

    for product in best_products:
        image_url = product.get('image', '')
        if not image_url or not is_image_valid(image_url):
            product['image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='

    ### Sección 5: Peores productos (con más de 500 reseñas y peor calificación o sin descuento)
    worst_products = df_clean[df_clean['no_of_ratings'] > 500]
    # Los peores productos se ordenan por baja calificación y por el peor descuento (o sin descuento)
    worst_products = worst_products.sort_values(by=['ratings', 'discount_price'], ascending=[True, True]).drop_duplicates(subset=['name']).head(3)

    worst_products_data = worst_products[['name', 'main_category', 'ratings', 'discount_price', 'actual_price', 'no_of_ratings', 'image', 'link']].to_dict(orient='records')

    for product in worst_products_data:
        image_url = product.get('image', '')
        if not image_url or not is_image_valid(image_url):
            product['image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='


    # Cálculos adicionales para indicadores
    # Categoría más rentable
    categoria_mas_rentable = df_clean.groupby('main_category')['profitability_usd'].sum().idxmax()

    # Categoría menos rentable
    categoria_menos_rentable = df_clean.groupby('main_category')['profitability_usd'].sum().idxmin()

    # Categoría con más objetos
    categoria_mas_objetos = df_clean['main_category'].value_counts().idxmax()

    # Categoría con menos objetos
    categoria_menos_objetos = df_clean['main_category'].value_counts().idxmin()

    # Categorías mejor rateadas (promedio de ratings)
    categorias_mejor_rateadas = df_clean.groupby('main_category')['ratings'].mean().idxmax()

    # Categorías peor rateadas (promedio de ratings)
    categorias_peor_rateadas = df_clean.groupby('main_category')['ratings'].mean().idxmin()

    # Cálculos para media y mediana de reseñas, precios y descuentos
    avg_reviews = df_clean['ratings'].mean()
    median_reviews = np.median(df_clean['ratings']) 

    avg_price = df_clean['actual_price'].mean()
    median_price = np.median(df_clean['actual_price'])

    # Calcular el porcentaje de descuento para cada producto
    df_clean['discount_percentage'] = ((df_clean['actual_price'] - df_clean['discount_price']) / df_clean['actual_price']) * 100

    # Calcular el promedio y la mediana del porcentaje de descuento
    avg_discount = round(df_clean['discount_percentage'].mean(), 2)
    median_discount = round(np.median(df_clean['discount_percentage']), 2)

    total_products = len(df_clean)
    products_with_active_discount = df_clean[df_clean['discount_price'] < df_clean['actual_price']]
    discount_percentage = round((len(products_with_active_discount) / total_products) * 100, 2)

    total_reviews = df_clean['no_of_ratings'].sum()

    # Ajustar todos los gráficos
    def adjust_figure(fig):
        fig.update_layout(
            margin=dict(l=10, r=10, t=150, b=10),
            autosize=True, 
            height=400, 
            width=500,
            title_x=0.5,  
        )
        return fig

    fig_category = adjust_figure(fig_category)
    fig_ratings = adjust_figure(fig_ratings)
    fig_price = adjust_figure(fig_price)
    fig_discount_price = adjust_figure(fig_discount_price)
    fig_reviews = adjust_figure(fig_reviews)
    fig_category_top_reviews = adjust_figure(fig_category_top_reviews)
    fig_category_top_discounts = adjust_figure(fig_category_top_discounts)
    fig_category_avg_price = adjust_figure(fig_category_avg_price)

    user_data = request.session.get('user', {})
    username = user_data.get('name', 'Usuario')
    user_id = user_data.get('user_id', None)
    roles = get_user_roles(user_id) if user_id else []
    role = roles[0] if roles else 'Rol no disponible'
    picture = user_data.get('picture', None)

    # Indicadores para la rentabilidad total en USD y % (ajustado)
    rentabilidad_total_usd = df_clean['profitability_usd'].sum()
    rentabilidad_total_percent = df_clean['profitability_percent'].mean()  # Rentabilidad en %

    satisfaction_index = df_clean['ratings'].mean() * 20

    fig_satisfaction = go.Figure(go.Indicator(
        mode="number+gauge",
        value=satisfaction_index,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'bgcolor': "lightgray",  # Color de fondo para la barra
            'borderwidth': 2,         # Grosor del borde
            'bordercolor': "black"     # Color del borde
        },
        title={'text': "Índice de Satisfacción del Cliente (%)"}
    ))

    fig_satisfaction.update_layout(
        margin=dict(l=10, r=10, t=150, b=10),
        autosize=True,
        height=350,
        width=500,
        title_x=0.5,
    )

    p_compra = 0.7        # 70% de probabilidad de compra
    p_insatisfaccion = 0.25 # 25% de probabilidad de insatisfacción
    p_devolucion = 0.8    # 80% de probabilidad de devolución si está insatisfecho

    # Calcular la probabilidad de devolución
    p_devolucion_total = p_compra * p_insatisfaccion * p_devolucion * 100  # Multiplicamos por 100 para expresarlo en porcentaje

    # Sección 5 - Pronósticos para 2024

    # Cálculo del precio promedio con descuento y precio actual para 2023
    avg_discount_price = df_clean['discount_price'].mean()
    avg_actual_price = df_clean['actual_price'].mean()

    # Factor de crecimiento (suponiendo un 5% de aumento para el próximo año)
    growth_factor = 1.05

    # Predicción de los precios para 2024 aplicando el factor de crecimiento
    predicted_discount_price = avg_discount_price * growth_factor
    predicted_actual_price = avg_actual_price * growth_factor

    # Cálculo de la calificación promedio ponderada para 2023
    df_clean['weighted_ratings'] = df_clean['ratings'] * df_clean['no_of_ratings']
    total_ratings = df_clean['no_of_ratings'].sum()
    total_weighted_ratings = df_clean['weighted_ratings'].sum()

    # Predicción de la calificación promedio para 2024 basada en el promedio ponderado
    predicted_avg_rating = total_weighted_ratings / total_ratings

    # Cálculo del margen de beneficio para cada producto
    df_clean['profit_margin'] = df_clean['actual_price'] - df_clean['discount_price']
    # Producto más rentable para 2023
    most_profitable_product = df_clean.loc[df_clean['profit_margin'].idxmax()]

    # Cálculo de la demanda ponderada para cada producto
    df_clean['demand_score'] = df_clean['ratings'] * df_clean['no_of_ratings']
    # Producto con mayor demanda
    highest_demand_product = df_clean.loc[df_clean['demand_score'].idxmax()]

    # Filtrar productos con más de 500 reseñas
    df_filtered = df_clean[df_clean['no_of_ratings'] > 500]

    # Obtener los productos más rentables para 2024 (suponiendo top 3 productos rentables) de los productos filtrados
    most_profitable_products = df_filtered.nlargest(3, 'profit_margin')[['name', 'main_category', 'ratings', 'no_of_ratings', 'discount_price', 'actual_price', 'image', 'link']]

    # Asegurarse de que los productos con mayor demanda no se repitan en los productos más rentables
    highest_demand_products = df_filtered.loc[~df_filtered['name'].isin(most_profitable_products['name'])] \
                                        .nlargest(3, 'demand_score')[['name', 'main_category', 'ratings', 'no_of_ratings', 'discount_price', 'actual_price', 'image', 'link']]

    # Si aún hay productos duplicados, los eliminamos y tomamos el siguiente producto
    remaining_products = df_filtered.loc[~df_filtered['name'].isin(most_profitable_products['name']) & ~df_filtered['name'].isin(highest_demand_products['name'])]

    # Añadir productos adicionales si no alcanzamos 3 en alguna lista (solo si es necesario)
    if len(most_profitable_products) < 3:
        remaining_profitable = remaining_products.nlargest(3 - len(most_profitable_products), 'profit_margin')
        most_profitable_products = pd.concat([most_profitable_products, remaining_profitable[['name', 'main_category', 'ratings', 'no_of_ratings', 'discount_price', 'actual_price', 'image', 'link']]])

    if len(highest_demand_products) < 3:
        remaining_demand = remaining_products.nlargest(3 - len(highest_demand_products), 'demand_score')
        highest_demand_products = pd.concat([highest_demand_products, remaining_demand[['name', 'main_category', 'ratings', 'no_of_ratings', 'discount_price', 'actual_price', 'image', 'link']]])

    # Evitar duplicados en ambas listas y asegurar que ambas tengan 3 productos
    final_most_profitable = pd.concat([most_profitable_products, remaining_products])\
                                .drop_duplicates(subset=['name'])\
                                .nlargest(3, 'profit_margin')

    final_highest_demand = pd.concat([highest_demand_products, remaining_products])\
                                .drop_duplicates(subset=['name'])\
                                .nlargest(3, 'demand_score')

    # Mostrar los resultados finales
    most_profitable_products = final_most_profitable.head(3)
    highest_demand_products = final_highest_demand.head(3)
    
    for product in most_profitable_products.itertuples():
        image_url = product.image
        if not image_url or not is_image_valid(image_url):
            most_profitable_products.at[product.Index, 'image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='

    for product in highest_demand_products.itertuples():
        image_url = product.image
        if not image_url or not is_image_valid(image_url):
            highest_demand_products.at[product.Index, 'image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='

    # Pasar los cálculos y gráficos a la plantilla
    return render(request, 'general.html', {
        'total_products': total_products,
        'category_counts': category_counts.to_dict(orient='records'),
        'fig_category': fig_category.to_html(full_html=False),
        'fig_ratings': fig_ratings.to_html(full_html=False),
        'fig_price': fig_price.to_html(full_html=False),
        'fig_discount_price': fig_discount_price.to_html(full_html=False),
        'fig_reviews': fig_reviews.to_html(full_html=False),
        'fig_category_top_reviews': fig_category_top_reviews.to_html(full_html=False),
        'fig_category_top_discounts': fig_category_top_discounts.to_html(full_html=False),
        'fig_category_avg_price': fig_category_avg_price.to_html(full_html=False),
        'profitability_products': profitability_products,
        'best_products': best_products,
        'worst_products_data': worst_products_data,
        'categoria_mas_rentable': categoria_mas_rentable,
        'categoria_menos_rentable': categoria_menos_rentable,
        'categoria_mas_objetos': categoria_mas_objetos,
        'categoria_menos_objetos': categoria_menos_objetos,
        'categorias_mejor_rateadas': categorias_mejor_rateadas,
        'categorias_peor_rateadas': categorias_peor_rateadas,
        'rentabilidad_total_usd': rentabilidad_total_usd,
        'rentabilidad_total_percent': rentabilidad_total_percent,
        'avg_reviews': avg_reviews,
        'median_reviews': median_reviews,
        'avg_price': avg_price,
        'median_price': median_price,
        'avg_discount': avg_discount,
        'median_discount': median_discount,
        'username': username,
        'role': role,
        'picture': picture,
        #satisfaction_index': satisfaction_index,
        'fig_satisfaction': fig_satisfaction.to_html(full_html=False),
        'discount_percentage': discount_percentage,
        'total_reviews': total_reviews,
        'p_devolucion_total': p_devolucion_total,
        'predicted_discount_price': predicted_discount_price,
        'predicted_actual_price': predicted_actual_price,
        'predicted_avg_rating': predicted_avg_rating,
        'most_profitable_product': most_profitable_product['name'],
        'profit_margin': most_profitable_product['profit_margin'],
        'highest_demand_product': highest_demand_product['name'],
        'demand_score': highest_demand_product['demand_score'],
        'most_profitable_products': most_profitable_products.to_dict(orient='records'),
        'highest_demand_products': highest_demand_products.to_dict(orient='records'),
    })