import React, { useEffect, useState } from 'react';
import axios from 'axios';  // Importa la librería Axios para realizar solicitudes HTTP
import './styles.css';

const ProductList = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetchProducts();  // Llama a la función para obtener los productos del backend
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get('/api/products/');  // Realiza una solicitud GET a la API de productos
      setProducts(response.data);  // Actualiza el estado con los productos recibidos
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <div>
      {products.map((product) => (
        <div key={product.id}>
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          <p>${product.price}</p>
          <p>Stock: {product.stock}</p>  // Agregado para mostrar el stock del producto
          {/* Otras representaciones visuales del producto */}
        </div>
      ))}
    </div>
  );
};

export default ProductList;

