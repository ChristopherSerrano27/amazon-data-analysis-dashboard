from django.shortcuts import render
from django.http import JsonResponse
import matplotlib.pyplot as plt
import seaborn as sns
from main.views import auth0_login_required
from .utils import import_and_clean_data

@auth0_login_required
def general_dashboard(request):
    df_clean = import_and_clean_data(data_folder='./dataset')

    if df_clean is None:
        return JsonResponse({"error": "No se pudo procesar los archivos."})

    total_products = df_clean.shape[0]
    category_counts = df_clean['main_category'].value_counts()
    price_stats = df_clean[['discount_price', 'actual_price']].describe()
    ratings_stats = df_clean['ratings'].describe()

    print(f"Total de productos: {total_products}")
    print("Productos por categoría:")
    print(category_counts)
    print("Estadísticas de precios:")
    print(price_stats)
    print("Estadísticas de calificaciones:")
    print(ratings_stats)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Gráfico 1: Distribución de productos por categoría (barras)
    axes[0, 0].bar(category_counts.index, category_counts.values, color='skyblue')
    axes[0, 0].set_title('Número de Productos por Categoría')
    axes[0, 0].set_xlabel('Categoría')
    axes[0, 0].set_ylabel('Número de Productos')
    axes[0, 0].tick_params(axis='x', rotation=45)

    # Gráfico 2: Distribución de calificaciones (histograma)
    sns.histplot(df_clean['ratings'], kde=True, bins=20, ax=axes[0, 1], color='green')
    axes[0, 1].set_title('Distribución de Calificaciones')
    axes[0, 1].set_xlabel('Calificación')
    axes[0, 1].set_ylabel('Frecuencia')

    # Gráfico 3: Histograma de precios
    sns.histplot(df_clean['discount_price'], kde=True, bins=20, ax=axes[1, 0], color='orange')
    axes[1, 0].set_title('Distribución de Precios con Descuento')
    axes[1, 0].set_xlabel('Precio con Descuento')
    axes[1, 0].set_ylabel('Frecuencia')

    # Gráfico 4: Histograma del número de reseñas
    sns.histplot(df_clean['no_of_ratings'], kde=True, bins=20, ax=axes[1, 1], color='purple')
    axes[1, 1].set_title('Distribución del Número de Reseñas')
    axes[1, 1].set_xlabel('Número de Reseñas')
    axes[1, 1].set_ylabel('Frecuencia')

    plt.tight_layout()

    plt.savefig('static/general_dashboard.png')
    plt.close()

    return render(request, 'general.html', {
        'total_products': total_products,
        'category_counts': category_counts.to_dict(),
        'price_stats': price_stats.to_dict(),
        'ratings_stats': ratings_stats.to_dict(),
        'chart_image': 'general_dashboard.png',
    })
