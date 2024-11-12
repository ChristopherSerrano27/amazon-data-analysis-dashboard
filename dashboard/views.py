from math import log
import plotly.express as px
from django.shortcuts import render
from main.views import auth0_login_required
from .utils import import_and_clean_data
from django.http import JsonResponse
from main.views import get_user_roles
import requests

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

    return render(request, 'general.html', {
        'username': username,
        'role': role,
        'picture': picture,
        'total_products': total_products,
        'category_counts': category_counts.to_dict(orient='records'),
        'fig_category': fig_category.to_html(full_html=False),
        'fig_ratings': fig_ratings.to_html(full_html=False),
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
    })
