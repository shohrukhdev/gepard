// Function to update the cart count display
function updateCartCount() {
    var totalItems = 0;
    for (var i = 0; i < localStorage.length; i++) {
        if (localStorage.key(i).startsWith('product_')) {
            totalItems += parseInt(localStorage.getItem(localStorage.key(i)), 10);
        }
    }
    document.getElementById('itemCount').textContent = totalItems;
}



function updateSingleTotal(productId){
    const totalSinglePriceUzs = document.getElementById("totalSinglePriceUzs");
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const itemIndex = cart.findIndex(item => item.id === productId);
    
    if (itemIndex !== -1) {
        totalSinglePriceUzs.innerHTML = Number(cart[itemIndex].qty * cart[itemIndex].price_uzs).toLocaleString()
    }
}

// Function to save item count to localStorage
function saveItemCount(productId, count) {
    localStorage.setItem('product_' + productId, count);
}

function increaseQuantity(itemId) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const itemIndex = cart.findIndex(item => item.id === itemId);
  
    if (itemIndex !== -1) {
      cart[itemIndex].qty = 1 + Number(cart[itemIndex].qty);
      localStorage.setItem('cart', JSON.stringify(cart));
      saveItemCount(itemId, cart[itemIndex].qty);
      updateCartCount();
      updateCartDisplay();
    }

    updateSingleTotal(itemId)
}

// Function to remove an item from the cart
function removeItem(productId, productName) {
    localStorage.removeItem('product_' + productId);
    updateSingleTotal(productId)
    
    // Show Toastify notification
    Toastify({
        text: "Товар удален из корзины",
        duration: 2000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: "#FF0000",
        stopOnFocus: true
    }).showToast();
}
  
function decreaseQuantity(itemId) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const itemIndex = cart.findIndex(item => item.id === itemId);
    const input = document.querySelector(".amountOfProduct");
    const setInput = document.querySelector(".amountOfSet");
    const setAmount = document.querySelector(".productSetAmount").value;

    let result = ((cart[itemIndex].qty - 1) / setAmount).toFixed(2)
    let amount = Number(cart[itemIndex].qty) - 1;

    if (input){
        input.value = amount;
        setInput.value = result;
    }
    
    cart[itemIndex].qty = amount;
    cart[itemIndex].set = result;

    if (itemIndex !== -1) {
      if (cart[itemIndex].qty === 0) {
        cart = cart.filter(item => item.id !== itemId);
        removeItem(itemId)
        if (cart.length == 0) {
            localStorage.removeItem('cart')
        }
      }
      localStorage.setItem('cart', JSON.stringify(cart));
    }
    localStorage.setItem('product_' + String(itemId), amount)
    // saveItemCount(itemId, cart[itemIndex].qty);
    updateCartCount();
    updateCartDisplay();
    updateSingleTotal(itemId)
}

function decreaseSetQuantity(itemId, setAmount) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    const itemIndex = cart.findIndex(item => item.id === itemId);
    const input = document.querySelector(".amountOfSet");
    const amountInput = document.querySelector(".amountOfProduct");
    let productAmount = (cart[itemIndex].set - 1) * Number(setAmount);

    if(cart[itemIndex].set == 0){
        return
    }
    
    if (input){
        input.value = Math.round(cart[itemIndex].set) - 1;
        amountInput.value = productAmount;
    }
    cart[itemIndex].qty = input.value * Number(setAmount);
    cart[itemIndex].set = input.value;

    if (itemIndex !== -1) {
      if (cart[itemIndex].set === 0) {
        cart = cart.filter(item => item.id !== itemId);
        removeItem(itemId)
        if (cart.length == 0) {
            localStorage.removeItem('cart')
        }
      }
      localStorage.setItem('cart', JSON.stringify(cart));
      localStorage.setItem('product_' + itemId, productAmount)
    }
    // saveItemCount(itemId, cart[itemIndex].qty);
    updateCartCount();
    updateCartDisplay();
    updateSingleTotal(itemId)
}

function deleteQuantity(itemId) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const itemIndex = cart.findIndex(item => item.id === itemId);
    cart.splice(itemIndex, 1);
    localStorage.setItem('cart', JSON.stringify(cart));

    removeItem(itemId);
    updateCartCount();
    updateCartDisplay();
    updateSingleTotal(itemId)
}

function updateCartDisplay() {
    const cartList = document.getElementById('cartList');
    const totalPrice = document.getElementById('totalPrice');
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    let total = 0;
    
    for (let i = 0; i < cart.length; i++){
        total = total + (parseInt(cart[i].price_uzs) * parseInt(cart[i].qty));
    }

    totalPrice.innerHTML = (total).toLocaleString();
    cartList.innerHTML = cart.map(item => `<div class="row cart-modal-item">
            <div class="col-4">
                <img src="${item.cover}" class="cart-product-cover" alt="">
            </div>
            <div class="col-6">
                <div class="cart-product-title">
                    <b>${item.name}</b>
                </div>
                <div class="cart-product-code">
                    Код: #${item.id}
                </div>

                <div class="cart-product-uzs">${Number(item.price_uzs).toLocaleString()} сум</div>
            </div>
            <div class="col-2" style="align-items: center; justify-content: center; display: flex;">
                <button onclick="deleteQuantity('${item.id}')" class="cart-delete-btn"><i class="fa fa-trash"></i></button>
            </div>
            <div class="row">
                <div class="col-6">
                    <b>Количество</b>
                </div>
                <div class="col-6 align-right">
                    <div>${item.amount}</div>
                </div>
            </div>
            <div class="col-2 pt-3 total-text">
                Общий:
            </div>
            <div class="col-10 pt-3">
                <div class="cart-counter-group">
                    <input type="hidden" name="productId" class="productId" value="${item.id}">
                    <input type="hidden" name="productName" class="productName" value="${item.name}">
                    <input type="hidden" name="productPriceUzs" class="productPriceUzs" value="${item.price_uzs}">
                    <input type="hidden" name="productCover" class="productCover" value="${item.cover}">
                    <input type="hidden" name="productTotalAmount" class="productTotalAmount" value="${item.amount}">
                    <div class="total-prices">
                        <div class="cart-total-uzs">${(item.price_uzs * item.qty).toLocaleString()} сум</div>
                    </div>
                    <button onclick="decreaseQuantity('${item.id}')">-</button>
                    <input 
                        type="text" 
                        onchange="updateFromInput(event)"  
                        data-item-id="${item.id}" 
                        value="${item.qty}" 
                        style="width: 50px !important;">
                    <button 
                        onclick="increaseQuantity('${item.id}')">+</button>
                </div>
            </div>
        </div>`).join('');

    // <li>
    //         <div>
    //             <span>${item.name} (${item.qty}x${item.price_uzs} сум) ${parseInt(item.qty) * parseInt(item.price_uzs)} сум</span><br>
    //         </div>
    //         <div class="cart-item-buttons">
    //             <button class="counter increase-counter" onclick="decreaseQuantity('${item.id}')">➖</button>
    //             <button class="counter decrease-counter" onclick="increaseQuantity('${item.id}')">➕</button>
    //             <button class="counter delete-counter" onclick="deleteQuantity('${item.id}')">🗑</button>
    //         </div>
    //     </li>
}


function updateFromInput(event) {
    const input = event.target;
    const itemId = input.getAttribute('data-item-id');
    const newQty = Number(input.value, 10);

    if (isNaN(newQty) || newQty < 1) {
        return
    }

    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    const itemIndex = cart.findIndex(item => item.id === itemId);
    if (itemIndex !== -1) {
        cart[itemIndex].qty = newQty;
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    localStorage.setItem(`product_${itemId}`, newQty)
    updateCartCount();
    updateCartDisplay();
    input.focus();
}


document.addEventListener('DOMContentLoaded', function () {

    // Function to get item count from localStorage
    function getItemCount(productId) {
        var count = localStorage.getItem('product_' + productId);
        return count ? parseInt(count, 10) : 0;
    }



    // Function to add an item to the cart
    function addItem(productId, productName, amount, productPriceUzs, cover, fullUpdate = false, set = 1, product_amoount = 0) {
        var currentCount = getItemCount(productId);
        var newCount = 0;
        if (fullUpdate){
            newCount = amount;
        }else {
            newCount = currentCount + amount; // Increase the count by the input amount            
        }
        saveItemCount(productId, newCount);

        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        const itemIndex = cart.findIndex(item => item.id === productId);
        const newSet = (newCount / set).toFixed(2);

        if (itemIndex === -1) {
            cart.push({ id: productId, name: productName, qty: newCount, set:newSet, price_uzs: productPriceUzs, cover:cover, amount:product_amoount});
        } else {
            cart[itemIndex].qty = newCount;
            cart[itemIndex].set = newSet;
        }

        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Show Toastify notification
        Toastify({
            text: "Товар добавлен в корзину",
            duration: 2000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "#4CAF50",
            stopOnFocus: true
        }).showToast();
        
        // Update the item count display
        updateSingleTotal(productId)
        updateCartCount();
        updateCartDisplay();
    }

    // Function to add an item to the cart
    function addItemSet(productId, productName, productPriceUzs, cover, setAmount, amount = 1, fullUpdate = false) {
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        const itemIndex = cart.findIndex(item => item.id === productId);
        let newProductAmount = setAmount * amount;

        if (itemIndex === -1) {
            cart.push({ id: productId, name: productName, qty: newProductAmount, set:amount, price_uzs: productPriceUzs, cover:cover });
        } else {
            if (fullUpdate === false){
                let oldAmount = Number(cart[itemIndex].set);
                cart[itemIndex].set = amount + oldAmount;
                
                newProductAmount = setAmount * (amount+oldAmount)
                cart[itemIndex].qty = newProductAmount;
            }else{
                newProductAmount = setAmount * amount;
                cart[itemIndex].set = amount;
                cart[itemIndex].qty = newProductAmount;
            }
        }

        localStorage.setItem('cart', JSON.stringify(cart));
        localStorage.setItem('product_' + String(productId), newProductAmount);
        
        // Show Toastify notification
        Toastify({
            text: "Товар добавлен в корзину",
            duration: 2000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "#4CAF50",
            stopOnFocus: true
        }).showToast();
        
        // Update the item count display
        updateSingleTotal(productId)
        updateCartCount();
        updateCartDisplay();
    }

    // Function to clear all items from the cart
    function clearCart() {
        localStorage.clear(); // Clear total count from localStorage
        updateCartCount(); // Update count display

        Toastify({
            text: "Корзина очищена",
            duration: 2000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "#ff006e",
            stopOnFocus: true
        }).showToast();

        updateCartDisplay();

    }

    // Add event listeners to all "Add to Cart" buttons
    document.querySelectorAll('.add-cart').forEach(function(button) {
        button.addEventListener('click', function() {
            var productId = this.getAttribute('data-item-id');
            var productName = this.getAttribute('data-item-name');
            var productPriceUzs = this.getAttribute('data-item-price-uzs');
            var productCover = this.getAttribute('data-item-cover');
            var productSet = this.getAttribute('data-item-set');
            var amount = this.getAttribute('data-item-amount');
                console.log("productSet", productSet)
                addItem(productId, productName, 1, productPriceUzs, productCover, fullUpdate = false, productSet, amount);
                document.querySelector('.amountOfProduct').value = getItemCount(productId);
                document.querySelector('.amountOfSet').value = (getItemCount(productId) / Number(productSet)).toFixed(2);
        });
    });

    document.querySelectorAll('.add-cart-set').forEach(function(button) {
        button.addEventListener('click', function() {
            var productId = this.getAttribute('data-item-id');
            var productName = this.getAttribute('data-item-name');
            var productPriceUzs = this.getAttribute('data-item-price-uzs');
            var productCover = this.getAttribute('data-item-cover');
            var productSet = this.getAttribute('data-item-set');
                addItemSet(productId, productName, productPriceUzs, productCover, productSet);
                document.querySelector('.amountOfProduct').value = getItemCount(productId);
                document.querySelector('.amountOfSet').value = (getItemCount(productId) / Number(productSet)).toFixed(2);
        });
    });

    if (document.querySelector(".amountOfProduct")){
        document.querySelector(".amountOfProduct").addEventListener("input", function() {
            let productId = document.querySelector(".productSingleId");
            let productName = document.querySelector(".productName");
            let productPriceUzs = document.querySelector(".productPriceUzs");
            let productCover = document.querySelector(".productCover");
            let productSet = document.querySelector(".productSetAmount");
            let amount = String(document.querySelector(".amountOfProduct").value).replace(",", ".");
            var product_amount = Number(document.querySelector(".productTotalAmount").value);
            
            if (productId){
                productId = productId.value;
            }
    
            if(productName){
                productName = productName.value;
            }
    
            if(productPriceUzs){
                productPriceUzs = productPriceUzs.value
            }

            if(productSet){
                productSet = productSet.value
            }

            if(productCover){
                productCover = productCover.value;
            }
    
            addItem(productId, productName, amount, productPriceUzs, productCover, fullUpdate = true, productSet, product_amount);
            document.querySelector('.amountOfSet').value = (getItemCount(productId) / Number(productSet)).toFixed(2);
        })
    }

    if (document.querySelector(".amountOfSet")){
        document.querySelector(".amountOfSet").addEventListener("input", function() {
            let productId = document.querySelector(".productSingleId");
            let productName = document.querySelector(".productName");
            let productPriceUzs = document.querySelector(".productPriceUzs");
            let productCover = document.querySelector(".productCover");
            let productSet = document.querySelector(".productSetAmount");
            
            if (productId){
                productId = productId.value;
            }
    
            if(productName){
                productName = productName.value;
            }
    
            if(productPriceUzs){
                productPriceUzs = productPriceUzs.value
            }
    
            if(productSet){
                productSet = Number(productSet.value)
            }
            if(productCover){
                productCover = productCover.value;
            }
            var amount = String(document.querySelector(".amountOfSet").value).replace(",", ".");
            console.log("productSet", amount)

            addItemSet(productId, productName, productPriceUzs, productCover, productSet, amount, fullUpdate = true);
            document.querySelector('.amountOfProduct').value = getItemCount(productId);
        })
    }

    

    // Add event listeners to all "Remove from Cart" buttons
    document.querySelectorAll('#deleteFromCart').forEach(function(button) {
        button.addEventListener('click', function() {
            var productId = this.getAttribute('data-item-id');
            var productName = this.getAttribute('data-item-name');
            removeItem(productId, productName);
            updateCartCount();
            updateCartDisplay();
        });
    });


    document.getElementById('clearCartButton').addEventListener('click', clearCart);

    // Initialize item count display on page load
    setTimeout(()=> {
        updateCartCount();
        updateCartDisplay();
        let itemId = document.querySelector(".productId");
        if (itemId){
            itemId = itemId.value;
        }
        updateSingleTotal(itemId)
    }, 300)

});