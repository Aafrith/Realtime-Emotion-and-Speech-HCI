"""
Test script for wake word detection
This helps verify the speech recognition is working properly
"""
import speech_recognition as sr
import time

def test_microphone():
    """Test if microphone is accessible"""
    print("=" * 60)
    print("MICROPHONE TEST")
    print("=" * 60)
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        print("✓ Microphone initialized successfully")
        
        # List available microphones
        print("\nAvailable microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  [{index}] {name}")
        
        return True
    except Exception as e:
        print(f"✗ Microphone error: {e}")
        return False

def test_ambient_noise():
    """Test ambient noise calibration"""
    print("\n" + "=" * 60)
    print("AMBIENT NOISE CALIBRATION")
    print("=" * 60)
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        print("Please be quiet for 2 seconds while calibrating...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
        
        print(f"✓ Calibration complete!")
        print(f"  Energy threshold: {recognizer.energy_threshold}")
        print(f"  Dynamic threshold: {recognizer.dynamic_energy_threshold}")
        
        return True, recognizer.energy_threshold
    except Exception as e:
        print(f"✗ Calibration error: {e}")
        return False, None

def test_basic_speech():
    """Test basic speech recognition"""
    print("\n" + "=" * 60)
    print("BASIC SPEECH RECOGNITION TEST")
    print("=" * 60)
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        # Configure recognizer
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        
        print("Say something (you have 5 seconds)...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        
        print("Processing...")
        text = recognizer.recognize_google(audio)
        print(f"✓ Recognized: '{text}'")
        return True
    except sr.WaitTimeoutError:
        print("✗ Timeout: No speech detected")
        return False
    except sr.UnknownValueError:
        print("✗ Could not understand audio")
        return False
    except sr.RequestError as e:
        print(f"✗ API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_wake_word_detection():
    """Test wake word detection specifically"""
    print("=" * 60)
    print("WAKE WORD DETECTION TEST")
    print("=" * 60)
    
    wake_word = "jarvis"
    print(f"Wake word: '{wake_word}'")
    print("Say the wake word (you have 5 seconds)...")
    
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        # Configure like in main app
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.5
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        
        print("Processing...")
        text = recognizer.recognize_google(audio).lower()
        print(f"Recognized: '{text}'")
        
        # Check if wake word detected
        wake_parts = wake_word.lower().split()
        text_clean = text.strip()
        
        if wake_word.lower() in text_clean:
            print(f"✓ EXACT MATCH! Wake word detected with high confidence (0.95)")
            return True
        elif all(part in text_clean for part in wake_parts):
            print(f"✓ PARTIAL MATCH! All words present (0.85 confidence)")
            return True
        else:
            matches = sum(1 for part in wake_parts if part in text_clean)
            if matches >= len(wake_parts) - 1 and matches > 0:
                print(f"✓ FUZZY MATCH! Most words present (0.75 confidence)")
                return True
            else:
                print(f"✗ No match. Detected {matches}/{len(wake_parts)} words")
                return False
                
    except sr.WaitTimeoutError:
        print("✗ Timeout: No speech detected")
        return False
    except sr.UnknownValueError:
        print("✗ Could not understand audio")
        return False
    except sr.RequestError as e:
        print(f"✗ API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def continuous_wake_word_test(duration=30):
    """Continuously listen for wake word"""
    print("\n" + "=" * 60)
    print("CONTINUOUS WAKE WORD LISTENING TEST")
    print("=" * 60)
    print(f"Listening for 'jarvis' for {duration} seconds...")
    print("Say 'jarvis' whenever you're ready")
    print("Press Ctrl+C to stop early")
    print()
    
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    # Configure
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    start_time = time.time()
    attempts = 0
    detections = 0
    
    try:
        while time.time() - start_time < duration:
            attempts += 1
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Listening (attempt {attempts})...", end='\r')
            
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                
                text = recognizer.recognize_google(audio).lower()
                print(f"[{elapsed}s] Heard: '{text}'                    ")
                
                if "jarvis" in text:
                    detections += 1
                    print(f"  ✓ WAKE WORD DETECTED! (Detection #{detections})")
                    print()
                
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                pass
            except Exception as e:
                print(f"\n  Error: {e}")
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    print(f"\nResults: {detections} detections in {attempts} attempts")
    return detections > 0

def main():
    print("\n" + "=" * 60)
    print("SPEECH RECOGNITION & WAKE WORD TESTING SUITE")
    print("=" * 60)
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Microphone
    total_tests += 1
    if test_microphone():
        tests_passed += 1
    
    # Test 2: Ambient noise
    total_tests += 1
    result, threshold = test_ambient_noise()
    if result:
        tests_passed += 1
    
    # Test 3: Basic speech
    total_tests += 1
    if test_basic_speech():
        tests_passed += 1
    
    # Test 4: Wake word detection
    total_tests += 1
    if test_wake_word_detection():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Wake word detection should work properly.")
    else:
        print("⚠ Some tests failed. Check the errors above.")
    
    # Optional: Continuous test
    print("\n" + "=" * 60)
    response = input("\nRun continuous wake word test? (y/n): ").strip().lower()
    if response == 'y':
        continuous_wake_word_test(30)
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
