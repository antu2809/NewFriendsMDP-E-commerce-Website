import React, { useState, useEffect } from 'react';

function Catalog() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // Lógica para obtener los datos de los productos desde el backend
    const fetchProducts = async () => {
      try {
        const response = await fetch('/api/products');
        const data = await response.json();
        setProducts(data);
      } catch (error) {
        console.error(error);
      }
    };

    fetchProducts();
  }, []);

  return (
    <div>
      <h1>Catálogo de productos</h1>
      {products.map((product) => (
        <div key={product.id}>
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          <p>${product.price}</p>
          <p>Stock: {product.stock}</p>
          {/* Otras representaciones visuales del producto */}
        </div>
      ))}
    </div>
  );
}

export default Catalog;
