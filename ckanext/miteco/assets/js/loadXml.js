
async function loadXml(){
    const file = document.getElementById("field-xml-upload").files[0];
    const reader = new FileReader(); 
    reader.addEventListener("load", () => {
        // this will then display a text file
        document.getElementById("xml-text").value = reader.result
    });
  
    reader.readAsText(file)
}