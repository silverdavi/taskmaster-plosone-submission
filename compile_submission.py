#!/usr/bin/env python3
"""
PLOS ONE Submission Compiler
Cleans, compiles, and prepares all documents for journal submission
"""

import os
import subprocess
import glob
import shutil
from pathlib import Path

def clean_latex_files():
    """Remove all LaTeX intermediate files"""
    print("🧹 Cleaning LaTeX intermediate files...")
    
    extensions_to_remove = [
        '*.aux', '*.log', '*.out', '*.toc', '*.lof', '*.lot', 
        '*.fls', '*.fdb_latexmk', '*.synctex.gz', '*.bbl', 
        '*.blg', '*.idx', '*.ind', '*.ilg', '*.nav', '*.snm', 
        '*.vrb', '*.figlist', '*.makefile', '*.bcf', '*.run.xml'
    ]
    
    for pattern in extensions_to_remove:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"   Removed: {file}")
            except OSError:
                pass

def run_pdflatex(tex_file, output_name=None):
    """Run pdflatex twice non-interactively"""
    print(f"📄 Compiling {tex_file}...")
    
    # First compilation
    cmd = [
        'pdflatex', 
        '-interaction=nonstopmode',  # Non-interactive mode
        '-halt-on-error',            # Stop on first error
        '-file-line-error',          # Better error reporting
        tex_file
    ]
    
    try:
        # First pass
        result1 = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result1.returncode != 0:
            print(f"❌ First pass failed for {tex_file}")
            print("STDOUT:", result1.stdout[-1000:])  # Last 1000 chars
            print("STDERR:", result1.stderr[-1000:])
            return False
            
        # Second pass for cross-references
        result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result2.returncode != 0:
            print(f"❌ Second pass failed for {tex_file}")
            print("STDOUT:", result2.stdout[-1000:])
            print("STDERR:", result2.stderr[-1000:])
            return False
            
        # Check if PDF was created
        pdf_file = tex_file.replace('.tex', '.pdf')
        if os.path.exists(pdf_file):
            print(f"✅ Successfully compiled {pdf_file}")
            
            # Rename if requested
            if output_name and output_name != pdf_file:
                shutil.move(pdf_file, output_name)
                print(f"📝 Renamed to: {output_name}")
            return True
        else:
            print(f"❌ PDF not created for {tex_file}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Compilation timed out for {tex_file}")
        return False
    except Exception as e:
        print(f"❌ Error compiling {tex_file}: {e}")
        return False

def create_track_changes():
    """Create track changes version using latexdiff"""
    print("🔄 Creating track changes version...")
    
    if not os.path.exists('old_submission.tex') or not os.path.exists('final.tex'):
        print("❌ Missing files for track changes (need old_submission.tex and final.tex)")
        return False
        
    try:
        # Run latexdiff
        cmd = ['latexdiff', 'old_submission.tex', 'final.tex']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ latexdiff failed: {result.stderr}")
            return False
            
        # Write output to track changes file
        with open('final_tracked_changes.tex', 'w') as f:
            f.write(result.stdout)
            
        print("✅ Track changes TeX file created")
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ latexdiff timed out")
        return False
    except Exception as e:
        print(f"❌ Error creating track changes: {e}")
        return False

def compile_all_documents():
    """Compile all four required documents"""
    print("🚀 Starting compilation process...")
    
    success_count = 0
    
    # 1. Compile main manuscript
    if run_pdflatex('final.tex', 'Manuscript.pdf'):
        success_count += 1
    
    # 2. Create and compile track changes
    if create_track_changes():
        if run_pdflatex('final_tracked_changes.tex', 'Revised Manuscript with Track Changes.pdf'):
            success_count += 1
    
    # 3. Compile response to reviewers
    if run_pdflatex('response_to_reviewers.tex', 'Response to Reviewers.pdf'):
        success_count += 1
    
    # 4. Compile supplementary information
    if run_pdflatex('supplementary.tex', 'Supporting Information.pdf'):
        success_count += 1
    
    return success_count

def check_files():
    """Check if all required files exist"""
    print("📋 Checking required input files...")
    
    required_files = [
        'final.tex',
        'old_submission.tex', 
        'response_to_reviewers.tex',
        'supplementary.tex'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Cannot proceed. Missing files: {missing_files}")
        return False
    
    return True

def check_dependencies():
    """Check if required tools are available"""
    print("🔧 Checking dependencies...")
    
    tools = ['pdflatex', 'latexdiff']
    missing_tools = []
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '--version'], capture_output=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Found: {tool}")
            else:
                missing_tools.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ Missing: {tool}")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n❌ Missing required tools: {missing_tools}")
        print("Please install them first (e.g., via MacTeX or TexLive)")
        return False
    
    return True

def summarize_results():
    """Show final results"""
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    expected_files = [
        'Manuscript.pdf',
        'Revised Manuscript with Track Changes.pdf', 
        'Response to Reviewers.pdf',
        'Supporting Information.pdf'
    ]
    
    success_count = 0
    for file in expected_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024*1024)  # MB
            print(f"✅ {file} ({size:.1f} MB)")
            success_count += 1
        else:
            print(f"❌ {file} - NOT CREATED")
    
    print(f"\n📈 SUCCESS RATE: {success_count}/{len(expected_files)} files created")
    
    if success_count == len(expected_files):
        print("\n🎉 ALL DOCUMENTS READY FOR PLOS ONE SUBMISSION!")
        print("\nNext steps:")
        print("1. Upload 'Manuscript.pdf' as the main manuscript")
        print("2. Upload 'Revised Manuscript with Track Changes.pdf' as track changes")
        print("3. Upload 'Response to Reviewers.pdf' as the rebuttal letter")
        print("4. Upload 'Supporting Information.pdf' as supplementary material")
        print("5. Upload figure files separately through PACE system")
    else:
        print(f"\n⚠️  Only {success_count} documents created successfully")

def main():
    """Main execution function"""
    print("🔬 PLOS ONE Submission Compiler")
    print("="*50)
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        return 1
    
    # Step 2: Check required files
    if not check_files():
        return 1
    
    # Step 3: Clean old files
    clean_latex_files()
    
    # Step 4: Compile all documents
    success_count = compile_all_documents()
    
    # Step 5: Clean up intermediate files again
    clean_latex_files()
    
    # Step 6: Show results
    summarize_results()
    
    return 0 if success_count == 4 else 1

if __name__ == "__main__":
    exit(main()) 