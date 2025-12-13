#!/usr/bin/env python3
"""Quick functional test of RPA modules."""

from rpa import RPA
import tempfile
import os

def test_all_modules():
    print("=" * 60)
    print("RPA Framework - Functional Test")
    print("=" * 60)

    bot = RPA()
    results = []

    # 1. Test Spreadsheet Module
    print("\n[1] Testing Spreadsheet Module...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_csv = f.name

        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        bot.spreadsheet.write_csv(data, temp_csv)
        df = bot.spreadsheet.read_csv(temp_csv)
        assert len(df) == 2
        os.unlink(temp_csv)
        print("   ✓ Spreadsheet module working")
        results.append(("Spreadsheet", True))
    except Exception as e:
        print(f"   ✗ Spreadsheet module failed: {e}")
        results.append(("Spreadsheet", False))

    # 2. Test File Module
    print("\n[2] Testing File Module...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            bot.files.write_text(test_file, "Hello World")
            content = bot.files.read_text(test_file)
            assert content == "Hello World"
            info = bot.files.get_info(test_file)
            assert info["is_file"] == True
        print("   ✓ File module working")
        results.append(("Files", True))
    except Exception as e:
        print(f"   ✗ File module failed: {e}")
        results.append(("Files", False))

    # 3. Test PDF Module
    print("\n[3] Testing PDF Module...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_pdf = f.name
        bot.pdf.create_from_text("Test PDF content", temp_pdf, title="Test")
        info = bot.pdf.get_info(temp_pdf)
        assert info["pages"] == 1
        os.unlink(temp_pdf)
        print("   ✓ PDF module working")
        results.append(("PDF", True))
    except Exception as e:
        print(f"   ✗ PDF module failed: {e}")
        results.append(("PDF", False))

    # 4. Test Documentation Module
    print("\n[4] Testing Documentation Module...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_docx = f.name
        bot.docs.create_word(temp_docx, title="Test Doc", content="Hello")
        text = bot.docs.extract_text_from_word(temp_docx)
        assert "Test Doc" in text
        os.unlink(temp_docx)
        print("   ✓ Documentation module working")
        results.append(("Docs", True))
    except Exception as e:
        print(f"   ✗ Documentation module failed: {e}")
        results.append(("Docs", False))

    # 5. Test Scraper Module
    print("\n[5] Testing Web Scraper Module...")
    try:
        soup = bot.scraper.get_soup("https://example.com")
        title = soup.find("title").text
        assert "Example" in title
        print("   ✓ Web scraper module working")
        results.append(("Scraper", True))
    except Exception as e:
        print(f"   ✗ Web scraper module failed: {e}")
        results.append(("Scraper", False))

    # 6. Test API Module
    print("\n[6] Testing API Module...")
    try:
        bot.api.configure(base_url="https://jsonplaceholder.typicode.com")
        users = bot.api.get("/users")
        assert len(users) > 0
        print("   ✓ API module working")
        results.append(("API", True))
    except Exception as e:
        print(f"   ✗ API module failed: {e}")
        results.append(("API", False))

    # 7. Test Database Module
    print("\n[7] Testing Database Module...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name

        bot.database.connect(f"sqlite:///{temp_db}")
        bot.database.create_table("users", {
            "id": "INTEGER",
            "name": "TEXT",
        }, primary_key="id")
        bot.database.insert("users", {"id": 1, "name": "Test"})
        rows = bot.database.query("users")
        assert len(rows) == 1
        bot.database.close()
        os.unlink(temp_db)
        print("   ✓ Database module working")
        results.append(("Database", True))
    except Exception as e:
        print(f"   ✗ Database module failed: {e}")
        results.append(("Database", False))

    # 8. Test Workflow
    print("\n[8] Testing Workflow...")
    try:
        workflow = bot.workflow("Test Workflow")
        workflow.add_step("Step 1", lambda: "result1")
        workflow.add_step("Step 2", lambda: "result2")
        result = workflow.run()
        assert result["status"] == "COMPLETED"
        assert len(result["steps"]) == 2
        print("   ✓ Workflow module working")
        results.append(("Workflow", True))
    except Exception as e:
        print(f"   ✗ Workflow module failed: {e}")
        results.append(("Workflow", False))

    # 9. Test Desktop Module (limited - just check import)
    print("\n[9] Testing Desktop Module...")
    try:
        size = bot.desktop.get_screen_size()
        assert size[0] > 0 and size[1] > 0
        print(f"   ✓ Desktop module working (screen: {size[0]}x{size[1]})")
        results.append(("Desktop", True))
    except Exception as e:
        print(f"   ✗ Desktop module failed: {e}")
        results.append(("Desktop", False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        icon = "✓" if status else "✗"
        print(f"  {icon} {name}")

    print(f"\nPassed: {passed}/{total}")
    print("=" * 60)

    bot.close()


if __name__ == "__main__":
    test_all_modules()
