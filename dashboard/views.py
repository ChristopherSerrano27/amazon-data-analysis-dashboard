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

    # Calcular el total de productos y la distribución de categorías
    total_products = len(df_clean)
    category_counts = df_clean['main_category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']

    # Crear gráficos
    fig_category = px.bar(category_counts, x='Category', y='Count', title='Distribución por Categoría')
    fig_ratings = px.histogram(df_clean, x='ratings', nbins=20, title='Distribución de Calificaciones')
    fig_discount_price = px.histogram(df_clean, x='discount_price', nbins=20, title='Distribución de Precios con Descuento')
    fig_reviews = px.histogram(df_clean, x='no_of_ratings', nbins=20, title='Distribución del Número de Reseñas')

    top_categories_reviews = df_clean.groupby('main_category')['no_of_ratings'].sum().sort_values(ascending=False).head(10)
    fig_category_top_reviews = px.bar(top_categories_reviews, x=top_categories_reviews.index, y=top_categories_reviews, title='Categorías con más Reseñas')

    top_discounted_categories = df_clean.groupby('main_category')['discount_price'].sum().sort_values(ascending=False).head(10)
    fig_category_top_discounts = px.bar(top_discounted_categories, x=top_discounted_categories.index, y=top_discounted_categories, title='Categorías con el Mayor Descuento')

    category_avg_price = df_clean.groupby('main_category')['actual_price'].mean().reset_index()
    fig_category_avg_price = px.bar(category_avg_price, x='main_category', y='actual_price', title='Precio Promedio por Categoría')

    # Filtrar los mejores productos con más de 500 o 750 reseñas, mejor rating y rebajas
    top_products = df_clean[df_clean['no_of_ratings'] >= 500]
    top_products = top_products.sort_values(by=['ratings', 'discount_price'], ascending=[False, False])

    # Eliminar productos duplicados por nombre
    top_products = top_products.drop_duplicates(subset=['name']).head(10)  # Limitar a los 10 mejores productos

    # Preparar datos para la sección de "Mejores Productos"
    best_products = top_products[['name', 'main_category', 'ratings', 'discount_price', 'actual_price', 'no_of_ratings', 'image', 'link']].to_dict(orient='records')

    # Validar imágenes de los productos y asignar imagen predeterminada si es necesario
    for product in best_products:
        image_url = product.get('image', '')  # Obtener la URL de la imagen
        if not image_url or not is_image_valid(image_url):
            # Si la URL de la imagen no es válida, asigna una imagen predeterminada
            product['image'] = 'https://media.istockphoto.com/id/1354776457/vector/default-image-icon-vector-missing-picture-page-for-website-design-or-mobile-app-no-photo.jpg?s=612x612&w=0&k=20&c=w3OW0wX3LyiFRuDHo9A32Q0IUMtD4yjXEvQlqyYk9O4='

    # Aplicar ajustes de tamaño y márgenes para evitar el desbordamiento
    def adjust_figure(fig):
        fig.update_layout(
            margin=dict(l=10, r=10, t=150, b=10),
            autosize=True, 
            height=400, 
            width=500,
            title_x=0.5,  
        )
        return fig

    # Ajustar todos los gráficos
    fig_category = adjust_figure(fig_category)
    fig_ratings = adjust_figure(fig_ratings)
    fig_discount_price = adjust_figure(fig_discount_price)
    fig_reviews = adjust_figure(fig_reviews)
    fig_category_top_reviews = adjust_figure(fig_category_top_reviews)
    fig_category_top_discounts = adjust_figure(fig_category_top_discounts)
    fig_category_avg_price = adjust_figure(fig_category_avg_price)

    # Obtener la información del usuario de la sesión
    user_data = request.session.get('user', {})
    username = user_data.get('name', 'Usuario')
    user_id = user_data.get('user_id', None)
    roles = get_user_roles(user_id) if user_id else []
    role = roles[0] if roles else 'Rol no disponible'

    picture = user_data.get('picture', None)

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
        'fig_category_avg_price': fig_category_avg_price.to_html(full_html=False),
        'fig_category_top_reviews': fig_category_top_reviews.to_html(full_html=False),
        'fig_category_top_discounts': fig_category_top_discounts.to_html(full_html=False),
        'best_products': best_products
    })
