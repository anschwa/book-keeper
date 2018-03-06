function getFormData() {
    const form = document.getElementById("book-form");
    const title = document.getElementById("title").value;
    const author = document.getElementById("author").value;
    const bookID = document.getElementById("id").value;
    var status = "";

    // find the selected book status
    var statuses = document.getElementsByName("status");
    for (var i = 0; i < statuses.length; i++) {
        if (statuses[i].checked) { status = statuses[i].value; }
    }

    // basic client side validation
    if (title.length === 0 || author.length === 0 || status.length === 0) {
        form.classList.add("error");
        return false;
    } else {
        form.classList.remove("error");
        const book = {"title": title, "author": author};
        return {"id": bookID, "book": book, "status": status};
    }

}

function resetForm() {
    const form = document.getElementById("book-form");
    const title = document.getElementById("title").value = "";
    const author = document.getElementById("author").value = "";

    var statuses = document.getElementsByName("status");
    for (var i = 0; i < statuses.length; i++) {
        statuses[i].checked = false;
    }
}

function formatBook(bookData) {
    const book = bookData["book"];

    var li = document.createElement("li");
    var div = document.createElement("div");
    div.classList.add("book");

    var info = document.createElement("div");
    info.classList.add("info");

    var title = document.createElement("span");
    title.classList.add("book-title");
    title.appendChild(document.createTextNode(book["title"]));

    var author = document.createElement("span");
    author.classList.add("book-author");
    author.appendChild(document.createTextNode(book["author"]));

    var bookID = document.createElement("input");
    bookID.type = "hidden";
    bookID.value = bookData["book_id"];
    bookID.classList.add("book-id");

    info.appendChild(title);
    info.insertAdjacentHTML("beforeend", "&nbsp;&ndash;&nbsp;");
    info.appendChild(author);

    var edit = document.createElement("span");
    edit.classList.add("edit");
    edit.classList.add("link");
    edit.appendChild(document.createTextNode("Edit"));

    var del = document.createElement("span");
    del.classList.add("delete");
    del.classList.add("link");
    del.appendChild(document.createTextNode("Delete"));

    var ops = document.createElement("div");
    ops.classList.add("ops");
    ops.appendChild(edit);
    ops.insertAdjacentHTML("beforeend", "&nbsp;|&nbsp;");
    ops.appendChild(del);
    ops.appendChild(bookID);

    div.appendChild(info);
    div.appendChild(ops);
    li.appendChild(div);
    return li;
}

// ---------- AJAX ---------- //

function addBook(request) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/book");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "json";
    xhr.onreadystatechange = function(e) {
        if (this.readyState === xhr.DONE && this.status === 201) {
            // console.log(this.response)
            resetForm();
            fetchBooks();
        } else {
            console.log(this.status, this.response);
            // show error message above form on the page
            // element.classList.add("api-error");
        }
    };
    xhr.send(JSON.stringify(request));
}

function editBook(bookID, request) {
    const xhr = new XMLHttpRequest();
    xhr.open("PATCH", "/book/"+bookID);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "json";
    xhr.onreadystatechange = function(e) {
        if (this.readyState === xhr.DONE && this.status === 200) {
            // console.log(this.response);
            resetForm();
            fetchBooks();
        } else {
            console.log(this.status, this.response);
            // show error message above form on the page
            // element.classList.add("api-error");
        }
    };
    xhr.send(JSON.stringify(request));
}

function deleteBook(bookID) {
    const xhr = new XMLHttpRequest();
    xhr.open("DELETE", "/book/"+bookID);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "json";
    xhr.onreadystatechange = function(e) {
        if (this.readyState === xhr.DONE && this.status === 204) {
            // console.log(this.response);
            fetchBooks();
        }
        console.log("readyState", this.readyState);
        console.log("status", this.status);
    };
    xhr.send();
}

function getBookID(event) {
    const ops = event.target.parentNode;
    const bookID = ops.getElementsByClassName("book-id")[0].value;
    return bookID;
}

function addEditListener() {
    var items = document.getElementsByClassName("edit");
    for (var i = 0; i < items.length; i++) {
        items[i].addEventListener("click", function(e) {
            resetForm();
            const bookID = getBookID(e);
            // move title and author into form
            const info = e.target.parentNode.parentNode;
            const title = info.getElementsByClassName("book-title")[0].innerText;
            const author = info.getElementsByClassName("book-author")[0].innerText;

            document.getElementById("title").value = title;
            document.getElementById("author").value = author;
            document.getElementById("id").value = bookID;

            location.href = "#top";
        });
    }
}

function addDeleteListener() {
    var items = document.getElementsByClassName("delete");
    for (var i = 0; i < items.length; i++) {
        items[i].addEventListener("click", function(e) {
            var sure = confirm("Are you sure you want to delete this book?");
            if (sure === true) {
                // show loading screen
                document.getElementById("loading").classList.remove("hidden");

                const bookID = getBookID(e);
                deleteBook(bookID);
            }
        });
    }
}

function fetchBooks() {
    // show loading screen
    document.getElementById("loading").classList.remove("hidden");

    const xhr = new XMLHttpRequest();
    xhr.open("GET", "/book");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "json";
    xhr.onreadystatechange = function(e) {
        if (this.readyState === xhr.DONE && this.status === 200) {
            // first clear out the old books
            const ols = document.getElementsByTagName("ol");
            for (var i = 0; i < ols.length; i++) {
                ols[i].innerHTML = "";
            }

            const library = this.response;
            for (var status in library) {
                const books = library[status];
                var section = document.getElementById(status+"-section");
                var bookList = section.getElementsByTagName("ol")[0];

                for (var i = 0; i < books.length; i++) {
                    const bookData = books[i];
                    bookList.appendChild(formatBook(bookData));
                }
            }

            // add event listeners to edit | delete buttons
            addEditListener();
            addDeleteListener();

            // hide the loading screen
            document.getElementById("loading").classList.add("hidden");
        } else {
            console.log(this.status, this.response);
        }
    };
    xhr.send();
}

// ------ Things to do after the page loads ------ //
window.addEventListener("DOMContentLoaded", function() {
    fetchBooks();

    // logout
    const logout = document.getElementById("logout");
    logout.addEventListener("click", function() {
        alert("Unfortunately, Basic Auth information is handled differently by every browser and cannot easily be cleared. Quitting the browser is the only reliable way to logout.");
    });

    // Add or Edit a book
    const submit = document.getElementById("submit");
    submit.addEventListener("click", function() {
        // show loading screen
        document.getElementById("loading").classList.remove("hidden");

        const data = getFormData();
        if (data) {
            const bookID = data["id"];

            if (bookID.length == 0) {
                // the :id field will be ignored by the database
                addBook(data);
            } else {
                const request = [{"op": "book", "value": data["book"]},
                                 {"op": "status", "value": data["status"]}];
                editBook(bookID, request);
            }
        }
    });
});
