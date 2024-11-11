import plotly.express as px
from django.shortcuts import render
from main.views import auth0_login_required
from .utils import import_and_clean_data
from django.http import JsonResponse
from main.views import get_user_roles  

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
    })
