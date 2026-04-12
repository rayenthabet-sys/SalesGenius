from gradio_client import Client

sales_client = Client("http://127.0.0.1:7860")
plot_client = Client("https://4a5b836a908645d289.gradio.live")

sales_result = sales_client.predict(
    message="Hello!!",
    history=[],
    company_name="Hello!!",
    sector="Healthcare",
    size="Micro (1-9 employees)",
    use_search=True,
    api_name="/process_chat",
)

print(sales_result)